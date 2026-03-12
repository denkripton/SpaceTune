from src.modules.music.repository import TrackRepository
from src.modules.auth.repository import UserRepository
from src.modules.music.schemas import (
    TrackCreationSchema,
    TrackMetadataReadShema,
    TrackReadSchema,
)
from src.aws.utils.actions import bucket_manager
from src.modules.music.config import logger
from src.modules.music.utils.duration import count_duration
from src.modules.auth.utils.hash_generation import pw_manager
from src.exceptions import Error

import uuid


class TrackService:
    def __init__(self, track_repo: TrackRepository, user_repo: UserRepository):
        self.__track_repo = track_repo
        self.__user_repo = user_repo

    async def create_track(
        self, user_id: str, data: TrackCreationSchema, music_file, image_file
    ):
        user_id = uuid.UUID(user_id)
        track_aws_key = f"track/{user_id}/{uuid.uuid4()}"
        image_aws_key = f"image/{user_id}/{uuid.uuid4()}"
        data = data.model_dump()
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise Error(code=422, msg="User does not exist")
        
        existing_track = await self.__track_repo.get_one(
            owner_id=user_id, name=data["name"]
        )

        if existing_track is not None:
            raise Error(code=422, msg="Track already exist")

        data["track_url"] = track_aws_key
        data["photo_url"] = image_aws_key
        data["owner_id"] = user_id
        data["duration"] = await count_duration(file=music_file)

        try:
            track = await self.__track_repo.create(**data)
            await self.__track_repo.session.commit()
            await self.__track_repo.session.refresh(track)
        except Exception as e:
            await self.__track_repo.session.rollback()
            logger.warning(e)

        bucket_manager.upload_file(
            file=music_file.file,
            file_type=music_file.content_type,
            key=track_aws_key,
        )
        bucket_manager.upload_file(
            file=image_file.file,
            file_type=image_file.content_type,
            key=image_aws_key,
        )
        return track

    async def delete_track(self, user_id, password, track_name):
        existing_user = await self.__user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise Error(code=422, msg="User does not exist")

        password_check = pw_manager.check_password(password, existing_user.password)

        if password_check is False:
            raise Error(code=403, msg="Incorrect password")

        existing_track = await self.__track_repo.get_one(
            owner_id=user_id, name=track_name
        )
        if existing_track is None:
            raise Error(code=422, msg="Track does not exist")
        bucket_manager.delete_file(key=existing_track.track_url)
        bucket_manager.delete_file(key=existing_track.photo_url)

        try:
            await self.__track_repo.delete_obj(id=existing_track.id)
            await self.__track_repo.session.commit()
        except Exception as e:
            await self.__track_repo.session.rollback()
            logger.warning(e)
        return "Track has been deleted succesfuly"

    async def get_track(self, track_name):

        existing_track = await self.__track_repo.get_one(name=track_name)
        if existing_track is None:
            raise Error(code=422, msg="Track does not exist")

        track = bucket_manager.presigned_url(key=existing_track.track_url)
        photo = bucket_manager.presigned_url(key=existing_track.photo_url)
        return {"metadata": existing_track, "audio": track, "image": photo}

    async def get_my_tracks(self, user_id):

        tracks = await self.__track_repo.get_many(owner_id=user_id)
        list_to_return = []

        # It looks terrible, but now I can't find any other solution
        for track in tracks:
            audio = bucket_manager.presigned_url(key=track.track_url)
            image = bucket_manager.presigned_url(key=track.photo_url)
            list_to_return.append(
                TrackMetadataReadShema(
                    metadata=TrackReadSchema(
                        id=track.id,
                        name=track.name,
                        artists=track.artists,
                        duration=track.duration,
                    ),
                    audio=audio,
                    image=image,
                )
            )

        return list_to_return
