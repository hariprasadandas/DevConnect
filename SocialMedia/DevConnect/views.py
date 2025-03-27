from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Comment,Like,User,Profile,Follow
from django.contrib.auth import authenticate, login, logout

# Home page view
@login_required
def home(request):
    posts = Post.objects.all().order_by('-created_at')
    comments = {post.id: post.comments.all() for post in posts}
    liked_posts = Like.objects.filter(user=request.user).values_list('post', flat=True)

    return render(request, 'home.html', {
        'posts': posts,
        'comments': comments,
        'liked_posts': liked_posts,
    })
def profile(request):
    user = request.user
    posts = Post.objects.filter(author=user)
    return render(request, 'profile.html', {'user': user, 'posts': posts})

# Myposts page view
@login_required
def myposts(request):
    posts = request.user.posts.all()

    return render(request, 'myposts.html', {
        'posts': posts,
    })
    
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        messages.error(request, "You are not authorized to edit this post.")
        return redirect('profile')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            post.content = content
            post.save()
            messages.success(request, "Post updated successfully.")
            return redirect('profile')

    return render(request, 'editpost.html', {'post': post})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        messages.error(request, "You are not authorized to delete this post.")
        return redirect('profile', user_id=request.user.id)

    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully.")
        return redirect('profile', user_id=request.user.id)

    return render(request, 'deletepost.html', {'post': post})


# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

# Login view
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

# Signup view
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        messages.success(request, "Account created successfully. You can now login.")
        return redirect('login')

    return render(request, 'signup.html')

# Create post view
@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            post = Post.objects.create(
                author=request.user,
                content=content
            )
            return redirect('home')
        else:
            messages.error(request, "Post content cannot be empty")
            return redirect('create_post')

    return render(request, 'create_post.html')

# Comment on a post view
# Comment on a post view
@login_required
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            comment = Comment(author=request.user, post=post, content=content)
            comment.save()
            return redirect('comment_post', post_id=post.id)
        else:
            messages.error(request, "Comment content cannot be empty.")
            return redirect('comment_post', post_id=post.id)

    comments = post.comments.all()  # Fetch comments for GET request
    return render(request, 'comment_post.html', {'post': post, 'comments': comments})


# Like a post view
@login_required
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()  # Remove like if already liked

    return redirect('home')


# --------------------------------------API VIEWS------------------------------------------------------------------------------------

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileSerializer, PostSerializer, LikeSerializer, CommentSerializer, FollowSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import re
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError




@api_view(['GET', 'POST'])
def api_profile_list(request):
    """API view to list all profiles or create a new user profile (signup)."""
    
    if request.method == 'GET':
        # Retrieve all user profiles
        users = User.objects.all()
        users_data = []
        
        for user in users:
            users_data.append({
                'username': user.username,
                'email': user.email,
            })
        
        return Response(users_data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Handle user signup
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Validate input fields
        if not username or not email or not password:
            return Response({'error': 'All fields (username, email, password) are required'},
                             status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response({'error': 'Invalid email format'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the user object
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Generate JWT tokens (access and refresh)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Return the tokens in the response
            return Response({
                'access_token': access_token,
                'refresh_token': str(refresh)
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


@api_view(['GET'])
def api_profile_view(request):
    """Returns the profile of the logged-in user."""
    if request.user.is_authenticated:
        profile_data = {
            "id": request.user.id,  # Adding the user's ID
            "username": request.user.username,
            "email": request.user.email,
        }
        return Response(profile_data, status=200)
    else:
        return Response({"error": "Authentication required."}, status=401)


from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User

@api_view(['GET'])
def get_user_profile(request, username):
    """API view to return the profile of another user by username."""
    try:
        # Retrieve the user by username
        user = User.objects.get(username=username)
        
        # Prepare the profile data
        profile_data = {
            "id": user.id, 
            "username": user.username,
            "email": user.email,
            "bio": user.profile.bio if hasattr(user, 'profile') and user.profile else None,  # Safe check
        }

        return Response(profile_data, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    

@api_view(['GET'])
def get_users(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        return Response({"error": "You must be logged in to view users."}, status=403)
    
    # Get all users excluding the logged-in user
    users = User.objects.exclude(id=request.user.id)
    serializer = UserSerializer(users, many=True)
    
    return Response(serializer.data)





@api_view(['GET', 'POST'])
def api_post_list(request):
    """API view to list all posts or create a new post."""
    if request.method == 'GET':
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True, context={'request': request})  # Add request to the context
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)  # Associate the post with the current user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET', 'PUT', 'DELETE'])
def api_post_detail(request, pk):
    """
    API view to retrieve, update, or delete a specific post.
    """
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

    # Retrieve a single post
    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data)

    # Update a post
    elif request.method == 'PUT':
        # Ensure the user is the author of the post
        if post.author != request.user:
            return Response({"error": "You do not have permission to edit this post."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Delete a post
    elif request.method == 'DELETE':
        # Ensure the user is the author of the post
        if post.author != request.user:
            return Response({"error": "You do not have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

from rest_framework.permissions import IsAuthenticated

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def api_mypost_list(request): 
    """API view to list all posts or create a new post."""
    
    if request.method == 'GET':
        # Get posts for the logged-in user
        posts = Post.objects.filter(author=request.user)  # Filter posts by the logged-in user
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Create a new post and associate it with the logged-in user
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)  # Save the post with the logged-in user as the author
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def api_like_post(request, post_id):
    """
    API view to like/unlike a post and fetch like details.
    Handles:
    - POST: Toggles like/unlike for the authenticated user.
    - GET: Retrieves the like count and list of users who liked the post.
    """
    try:
        post = Post.objects.get(id=post_id) 
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Toggle like/unlike
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            like.delete()  # Unlike the post
            return Response({
                "message": "Like removed",
                "like_count": post.likes.count(),
                "users": [{"id": like.user.id, "username": like.user.username} for like in post.likes.all()]
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Post liked",
            "like_count": post.likes.count(),
            "users": [{"id": like.user.id, "username": like.user.username} for like in post.likes.all()]
        }, status=status.HTTP_201_CREATED)

    elif request.method == 'GET':
        # Retrieve like details
        likes = Like.objects.filter(post=post)
        return Response({
            "like_count": likes.count(),
            "users": [{"id": like.user.id, "username": like.user.username} for like in likes]
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
def api_comment_list(request, post_id):
    """API view to list all comments for a post or create a new comment."""
    try:
        # Fetch the post by its ID
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Retrieve all comments for the specified post
        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Handle the creation of a new comment
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            # Save the comment with the logged-in user as the author and the post as the target
            serializer.save(author=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAuthenticated

@api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])  # Ensures only authenticated users can follow/unfollow
def api_follow_list(request, user_id):
    """
    API view to toggle follow/unfollow and fetch follow details.
    Handles:
    - POST: Toggles follow/unfollow for the authenticated user.
    - GET: Retrieves the follower count and list of followers for a user.
    """
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Toggle follow/unfollow
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
        
        if not created:
            follow.delete()  # Unfollow the user
            return Response({
                "message": "Unfollowed successfully",
                "follower_count": Follow.objects.filter(following=target_user).count(),
                "followers": [follow.follower.username for follow in Follow.objects.filter(following=target_user)]
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Followed successfully",
            "follower_count": Follow.objects.filter(following=target_user).count(),
            "followers": [follow.follower.username for follow in Follow.objects.filter(following=target_user)]
        }, status=status.HTTP_201_CREATED)

    elif request.method == 'GET':
        # Retrieve follow details
        followers = Follow.objects.filter(following=target_user)
        return Response({
            "follower_count": followers.count(),
            "followers": [follow.follower.username for follow in followers]
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# @api_view(['GET', 'POST'])
# def api_follow_list(request, user_id):
#     """
#     API view to toggle follow/unfollow and fetch follow details.
#     Handles:
#     - POST: Toggles follow/unfollow for the authenticated user.
#     - GET: Retrieves the follower count and list of followers for a user.
#     """
#     try:
#         target_user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'POST':
#         # Toggle follow/unfollow
#         follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
#         if not created:
#             follow.delete()  # Unfollow the user
#             return Response({
#                 "message": "Unfollowed successfully",
#                 "follower_count": Follow.objects.filter(following=target_user).count(),
#                 "followers": [follow.follower.username for follow in Follow.objects.filter(following=target_user)]
#             }, status=status.HTTP_200_OK)

#         return Response({
#             "message": "Followed successfully",
#             "follower_count": Follow.objects.filter(following=target_user).count(),
#             "followers": [follow.follower.username for follow in Follow.objects.filter(following=target_user)]
#         }, status=status.HTTP_201_CREATED)

#     elif request.method == 'GET':
#         # Retrieve follow details
#         followers = Follow.objects.filter(following=target_user)
#         return Response({
#             "follower_count": followers.count(),
#             "followers": [follow.follower.username for follow in followers]
#         }, status=status.HTTP_200_OK)

#     return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

