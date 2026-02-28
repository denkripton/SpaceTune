from src.modules.music.repository import TrackRepository
from src.modules.auth.repository import UserRepository
from src.modules.music.schemas import TrackCreationSchema
from src.aws.utils.actions import bucket_manager
from src.modules.music.utils.duration import count_duration
from src.modules.auth.utils.hash_generation import pw_manager

from fastapi import HTTPException
import uuid


class TrackService:
    def __init__(self, track_repo: TrackRepository, user_repo: UserRepository):
        self.track_repo = track_repo
        self.user_repo = user_repo

    async def create_track(
        self, user_id: str, data: TrackCreationSchema, music_file, image_file
    ):
        user_id = uuid.UUID(user_id)
        track_aws_key = f"track/{user_id}/{uuid.uuid4()}"
        image_aws_key = f"image/{user_id}/{uuid.uuid4()}"
        data = data.model_dump()
        existing_user = await self.user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")
        data["track_url"] = track_aws_key
        data["photo_url"] = image_aws_key
        data["owner_id"] = user_id
        data["duration"] = await count_duration(file=music_file)

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
        track = await self.track_repo.create(**data)
        await self.track_repo.session.commit()
        await self.track_repo.session.refresh(track)

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
        existing_user = await self.user_repo.get_by_id(id=user_id)

        if existing_user is None:
            raise HTTPException(status_code=422, detail="User does not exist")

        password_check = pw_manager.check_password(password, existing_user.password)

        if password_check is False:
            raise HTTPException(status_code=422, detail="Incorrect password")

        existing_track = await self.track_repo.get_one(
            owner_id=user_id, name=track_name
        )
        if existing_track is None:
            raise HTTPException(status_code=422, detail="Track does not exist")
        bucket_manager.delete_file(key=existing_track.track_url)
        bucket_manager.delete_file(key=existing_track.photo_url)

        try:
            await self.track_repo.delete_obj(id=existing_track.id)
            await self.track_repo.session.commit()
        except Exception as e:
            await self.track_repo.session.rollback()
            print(e)
        return "Track has been deleted succesfuly"
