import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from src.aws import bucket_manager
from src.modules.auth.repository import UserRepository
from src.modules.grades.repository import GradeRepository
from src.modules.music.config import logger
from src.modules.music.repository import TrackRepository
from src.modules.music.schemas.track.creation import TrackCreationSchema
from src.modules.music.schemas.track.media import MediaURLsSchema
from src.modules.music.schemas.track.metadata import TrackMetadataReadShema
from src.modules.music.schemas.track.read import TrackReadSchema
from src.modules.music.utils import count_duration
from src.modules.music.utils.enums import FileSizeLimit, MediaTypes
from src.utils.exceptions import FileSizeLimitExceeded, ServiceError
from src.utils.uploads import SizeLimitedStream


class TrackService:
    def __init__(
        self,
        track_repo: TrackRepository,
        user_repo: UserRepository,
        grade_repo: GradeRepository,
    ):
        self.__track_repo = track_repo
        self.__user_repo = user_repo
        self.__grade_repo = grade_repo

    async def create_track(
        self, user_id: str, data: TrackCreationSchema, music_file, image_file
    ):
        user_id = uuid.UUID(user_id)
        data = data.model_dump()
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        track_aws_key = f"track/{user_id}/{uuid.uuid4()}"
        image_aws_key = f"image/{user_id}/{uuid.uuid4()}"

        existing_track = await self.__track_repo.get_one(
            owner_id=user_id, name=data["name"]
        )

        if existing_track is not None:
            raise ServiceError(code=422, msg="Track already exist")

        if music_file.content_type not in MediaTypes.AUDIO_TYPES.value:
            raise ServiceError(code=422, msg="Invalid audio file type")

        if image_file.content_type not in MediaTypes.IMAGE_TYPES.value:
            raise ServiceError(code=422, msg="Invalid image file type")

        if (
            music_file.size is not None
            and music_file.size > FileSizeLimit.MAX_AUDIO_SIZE.value
        ):
            raise ServiceError(code=422, msg="Audio file is too big")

        if (
            image_file.size is not None
            and image_file.size > FileSizeLimit.MAX_IMAGE_SIZE.value
        ):
            raise ServiceError(code=422, msg="Image file is too big")

        data["track_url"] = track_aws_key
        data["photo_url"] = image_aws_key
        result_artists = [existing_user.username]

        for artist in data["artists"]:
            result_artists.append(artist)
        data["artists"] = result_artists

        data["owner_id"] = user_id
        data["duration"] = await count_duration(file=music_file)

        try:
            bucket_manager.upload_file(
                file=music_file.file,
                file_type=music_file.content_type,
                key=track_aws_key,
            )
            limited_image_stream = SizeLimitedStream(
                image_file.file, max_bytes=FileSizeLimit.MAX_IMAGE_SIZE.value
            )
            bucket_manager.upload_file(
                file=limited_image_stream,
                file_type=image_file.content_type,
                key=image_aws_key,
            )
        except FileSizeLimitExceeded as e:
            bucket_manager.delete_file(key=track_aws_key)
            raise ServiceError(code=422, msg="Image file is too big") from e
        except Exception as e:
            bucket_manager.delete_file(key=track_aws_key)
            raise ServiceError(code=500, msg="Failed to upload media") from e

        try:
            track = await self.__track_repo.create(**data)
            await self.__track_repo.session.commit()
            await self.__track_repo.session.refresh(track)
        except IntegrityError as e:
            await self.__track_repo.session.rollback()
            bucket_manager.delete_file(key=track_aws_key)
            bucket_manager.delete_file(key=image_aws_key)
            logger.warning(e)
            raise ServiceError(code=422, msg="Track already exist") from e
        except Exception as e:
            await self.__track_repo.session.rollback()
            bucket_manager.delete_file(key=track_aws_key)
            bucket_manager.delete_file(key=image_aws_key)
            logger.warning(e)
            raise ServiceError(code=500, msg="Failed to save track") from e

        metadata = TrackReadSchema(
            id=track.id,
            name=track.name,
            artists=track.artists,
            duration=track.duration,
            released=datetime.strftime(track.created_at, "%Y-%m-%d"),
        )

        return metadata

    async def delete_track(self, user_id, track_id):
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise ServiceError(code=422, msg="User does not exist")

        existing_track = await self.__track_repo.get_one(id=track_id, owner_id=user_id)
        if existing_track is None:
            raise ServiceError(code=422, msg="Track does not exist")

        bucket_manager.delete_file(key=existing_track.track_url)
        bucket_manager.delete_file(key=existing_track.photo_url)

        try:
            await self.__track_repo.delete_obj(id=existing_track.id)
            await self.__track_repo.session.commit()
        except Exception as e:
            await self.__track_repo.session.rollback()
            logger.warning(e)
            raise ServiceError(code=500, msg="Failed to delete track") from e

        return "Track has been deleted succesfuly"

    async def get_track(self, track_id):

        existing_track = await self.__track_repo.get_by_id(id=track_id)
        if existing_track is None:
            raise ServiceError(code=422, msg="Track does not exist")

        aggregates = await self.__grade_repo.get_aggregates_by_track_ids(
            [existing_track.id]
        )
        avg_grade, ratings_count = aggregates.get(existing_track.id, (0, 0))

        metadata = TrackReadSchema(
            id=existing_track.id,
            name=existing_track.name,
            artists=existing_track.artists,
            duration=existing_track.duration,
            average_grade=avg_grade,
            number_of_ratings=ratings_count,
            released=datetime.strftime(existing_track.created_at, "%Y-%m-%d"),
        )

        audio = bucket_manager.presigned_url(key=existing_track.track_url)
        image = bucket_manager.presigned_url(key=existing_track.photo_url)

        media = MediaURLsSchema(audio=audio, image=image)

        return {"metadata": metadata, "media": media}

    async def get_my_tracks(self, user_id):

        tracks = await self.__track_repo.get_many(owner_id=user_id)
        track_ids = [track.id for track in tracks]

        aggregates = await self.__grade_repo.get_aggregates_by_track_ids(track_ids)

        list_to_return = []

        for track in tracks:
            audio = bucket_manager.presigned_url(key=track.track_url)
            image = bucket_manager.presigned_url(key=track.photo_url)

            avg_grade, ratings_count = aggregates.get(track.id, (0, 0))

            list_to_return.append(
                TrackMetadataReadShema(
                    metadata=TrackReadSchema(
                        id=track.id,
                        name=track.name,
                        artists=track.artists,
                        duration=track.duration,
                        average_grade=avg_grade,
                        number_of_ratings=ratings_count,
                        released=datetime.strftime(track.created_at, "%Y-%m-%d"),
                    ),
                    media=MediaURLsSchema(audio=audio, image=image),
                )
            )

        return list_to_return
