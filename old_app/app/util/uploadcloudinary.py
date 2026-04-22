async def upload_avatar(file, user_id: str):
    result = cloudinary.uploader.upload(
        file.file,
        folder="avatars",
        public_id=user_id,
        overwrite=True,
        resource_type="image"
    )
    return result["secure_url"]



avatars/{user_id}