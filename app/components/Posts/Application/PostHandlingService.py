from app.Shared.Supabase.Domain.Supabase import Supabase
from app.components.Posts.Domain.Post import Post
from uuid import UUID

class PostHandlingService:
    def __init__(self):
        self.supabase = Supabase()

    def create_post(self, post: Post):
        self.supabase.insert_data("posts", post.__dict__)

    def get_post(self, id: UUID):
        return self.supabase.select_data("posts", ["*"]).data[id]

    def get_all_posts(self):
        return self.supabase.select_data("posts", ["*"]).data

    def update_post(self, post: Post):
        self.supabase.update_data("posts", post.__dict__, post.id)

    def delete_post(self, id: UUID):
        self.supabase.delete_data("posts", id)