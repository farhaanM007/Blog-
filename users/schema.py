from graphene import ObjectType, relay
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model
from graphql_jwt.decorators import login_required
import graphql_jwt
from .models import Blog,Comment
from graphql_relay import from_global_id
import re


class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        fields = "__all__"
        interfaces = (relay.Node,)
        filter_fields = {
            'author__username': ['exact'],
            
            
            
        }

class AppUser(DjangoObjectType):
    class Meta:
        model = get_user_model()

class CommentNode(DjangoObjectType):
    class Meta:
        model=Comment
        fields='__all__'
        interfaces=(relay.Node,)
        filter_fields={
            
        }

class BlogConnetion(relay.Connection):
    class Meta:
        node=BlogNode


#Blog create,update,delete mutations


class CreateBlog(relay.ClientIDMutation):
    
    """
        Creates a new blog post.

        Args:
            root: The root info of the mutation.
            info: The information about the GraphQL request.
            title: The title of the blog post.
            content: The content/body of the blog post (optional).

        Returns:
            CreateBlog: An object with the newly created blog post and success status.
            
        Raises:
            Exception: If the mutation encounters an error while creating the blog post.
        """ 
    class Input:
        title=graphene.String(required=True)
        content=graphene.String()
        
    blog=graphene.Field(BlogNode)
    success=graphene.Boolean()
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, title:str, content:str=None)->'CreateBlog':
        user=info.context.user
        if content is None:
            content=""
        blog = Blog(title=title, content=content, author=user)
        blog.save()

        return CreateBlog(blog=blog,success=True)

class UpdateBlog(relay.ClientIDMutation):
    
    """
    Updates an existing blog post.

    Args:
        root: The root info of the mutation.
        info: The information about the GraphQL request.
        id: The ID of the blog post to be updated.
        title: The new title to update the blog post (optional).
        content: The new content/body to update the blog post (optional).

    Returns:
        UpdateBlog: An object with the updated blog post and success status.

    Raises:
        PermissionError: If the requesting user doesn't have permission to update the blog post.
        Exception: If the specified blog post doesn't exist.
    """
    class Input:
        title=graphene.String(required=False,null=True)
        content=graphene.String(required=False,null=True)
        id=graphene.String(required=True,null=False)
    
    blog=graphene.Field(BlogNode)
    success=graphene.Boolean()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info,id:str, title:str=None, content:str=None)->'UpdateBlog':
        try:
            encoded_id=id
            decoded_id=from_global_id(encoded_id).id
            blog=Blog.objects.get(pk=decoded_id)
            if blog.author!=info.context.user:
                raise PermissionError("User has no permission")
            else:
                if title is None:
                    blog.title=blog.title
                else:
                    blog.title=title
                if content is None:
                    blog.content=blog.content
                else:
                    blog.content=content
                blog.save()
                
                return UpdateBlog(blog=blog,success=True)
        except Blog.DoesNotExist:
            raise Exception("Blog does not exist")


class DeleteBlog(relay.ClientIDMutation):
    """
        Performs deletion of the blog post.

        Args:
            root: The root object of the mutation.
            info: Information about the GraphQL request.
            id (str): The global ID of the blog post to be deleted.

        Returns:
            DeleteBlog: An object containing the success status of the mutation.

        Raises:
            PermissionError: If the user attempting to delete the blog post is not the author.
            Exception: If the blog post with the provided ID does not exist.
    """
    class Input:
        id=graphene.String(required=True,null=False)
        
    success=graphene.Boolean()
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info,id:str)->'DeleteBlog':
        try:
            encoded_id=id
            decoded_id=from_global_id(encoded_id).id
            blog=Blog.objects.get(pk=decoded_id)
            if blog.author!=info.context.user:
                raise PermissionError("User has no permission")
            else:
                blog.delete()
            return DeleteBlog(success=True)
        
        except Blog.DoesNotExist:
            raise Exception("BLog does not exist")

#Create,Delete comment mutation

class CreateComment(relay.ClientIDMutation):
    
    """
    Creates a new comment and associates it with a blog post.

    Args:
        root: The root info of the mutation.
        info: The information about the GraphQL request.
        blog_id: The ID of the blog post to which the comment is associated.
        body: The content/body of the comment.
        name: The name of the commenter(optional).
        email: The email of the commenter(optional).

    Returns:
        CreateComment: An object with the created comment and success status.

    Raises:
        ValueError: If the email format is invalid.
        Exception: If the specified blog does not exist.
    """
    
    class Input:
        blog_id=graphene.String()
        name=graphene.String(required=False)
        email=graphene.String(required=False)
        body=graphene.String()
    
    success=graphene.Boolean()
    comment=graphene.Field(CommentNode)
    
    @classmethod
    def mutate_and_get_payload(cls, root, info, blog_id:str,body:str,name:str=None,email:str=None)->'CreateComment':
        
        
        if name is None:
            name=""
        
        if email is None:
            email=""
        else:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValueError("Invalid email format")
            
        try:
            
            encoded_id=blog_id
            decoded_id=from_global_id(encoded_id).id
            blog=Blog.objects.get(pk=decoded_id)
            comment=Comment(blog=blog,name=name,email=email,body=body) 
            comment.save()
            return CreateComment(comment=comment,success=True)
        
        except Blog.DoesNotExist:
            raise Exception("Blog does Not exist")


class DeleteComment(relay.ClientIDMutation):
    
    """
    Mutation to delete a comment by the author of the blog the comment is part of.

    Args:
        comment_id (str): The global ID of the comment to be deleted.
    
    Returns:
        DeleteComment: An object containing the success status of the mutation.

    Raises:
        PermissionError: If the user attempting to delete the comment is not the author of the blog post.
        Exception: If the comment with the provided ID does not exist.
    """
    
    class Input:
        comment_id=graphene.String()
    
    success=graphene.Boolean(default_value=False)
    
    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, comment_id:str)->'DeleteComment':
        try:
            encoded_comment_id=comment_id
            decoded_id=from_global_id(encoded_comment_id).id
            comment=Comment.objects.get(pk=decoded_id)
            blog=comment.blog
            if blog.author!=info.context.user:
                raise PermissionError("User has no permission")
            else:
                comment.delete()
            return DeleteBlog(success=True)
        
        except Comment.DoesNotExist:
            raise Exception("Comment does not exist")
        

#User Login mutation

class CreateAppUser(graphene.Mutation):
    """
    Mutation to create a new User.

    Args:
        username (str): The username for the new user. (Required)
        password (str): The password for the new user. (Required)
    Returns:
            CreateAppUser: An object containing the success status and the newly created User.
    """
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    app_user = graphene.Field(AppUser)
    
    def mutate(self, info, username:str, password:str)->'CreateAppUser':
        app_user_model = get_user_model()
        new_user = app_user_model.objects.create(username=username)
        new_user.set_password(password)
        new_user.save()
        return CreateAppUser(app_user=new_user, success=True)


class Query(ObjectType):
    
    """
    Root query object for the application.
    """
    
    users = graphene.List(AppUser, description="List of all users in the system.")
    logged_in = graphene.Field(AppUser, description="Currently logged in user.")
    blogs = DjangoFilterConnectionField(BlogNode,description="Filtered list of all blog posts.")
    blog=graphene.Field(BlogNode,id=graphene.String(description="Global ID of the blog post."))
    comments=DjangoFilterConnectionField(CommentNode,description="Filtered list of all comments.")
    comments_for_blog=graphene.List(CommentNode,id=graphene.String(),description="Comments for a specific blog post by ID.")
    
    
    def resolve_blogs(self, info,**kwargs):
        
        """
        Resolves the list of all blog posts, ordered by their creation id in descending order.
        """
        
        return Blog.objects.all().order_by('-id')
    
    @login_required
    def resolve_blog(self, info,id:str):
        
        """
        Resolves a specific blog post by its global ID.
        """
        
        decoded_id=from_global_id(id).id
        return Blog.objects.prefetch_related('comments').get(id=decoded_id)
    
    def resolve_users(self, info):
        
        """
        Resolves a list of all users in the system.
        """
        
        return get_user_model().objects.all()
    
    @login_required
    def resolve_logged_in(self, info):
        
        """
        Resolves the currently logged in user.
        """
        
        return info.context.user
    
    @login_required
    def resolve_comments(self, info):
        
        """
        Resolves a list of all comments in the system.
        """
        
        return Comment.objects.all()
    
    
    def resolve_comments_for_blog(self, info,id:str):
        
        """
        Resolves a list of comments for a specific blog post by its global ID.
        """
        
        decoded_id=from_global_id(id).id
        return Comment.objects.filter(blog=decoded_id)


class Mutation(ObjectType):
    
    """
    Root mutation object for the application.
    """
    
    create_user = CreateAppUser.Field()
    create_blog=CreateBlog.Field()
    update_blog=UpdateBlog.Field()
    delete_blog=DeleteBlog.Field()
    create_comment=CreateComment.Field()
    delete_comment=DeleteComment.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
