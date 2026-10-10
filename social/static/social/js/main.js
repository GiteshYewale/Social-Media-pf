/**
 * SocialPulse - Dynamic Interactivity & AJAX Handles
 */

document.addEventListener('DOMContentLoaded', () => {

    // Helper to extract Django CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Toast notification auto dismiss
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    });

    // Post Character Counter & Image Preview
    const postContentInput = document.getElementById('post-content-input');
    const charCounter = document.getElementById('char-counter');
    const postImageInput = document.getElementById('post-image-input');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removePreviewBtn = document.getElementById('remove-preview-btn');

    if (postContentInput && charCounter) {
        postContentInput.addEventListener('input', () => {
            const currentLen = postContentInput.value.length;
            charCounter.textContent = `${currentLen}/500`;
            if (currentLen > 450) {
                charCounter.style.color = '#ef4444';
            } else {
                charCounter.style.color = 'var(--text-light)';
            }
        });
    }

    if (postImageInput && imagePreviewContainer && imagePreview) {
        postImageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    imagePreview.src = event.target.result;
                    imagePreviewContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        if (removePreviewBtn) {
            removePreviewBtn.addEventListener('click', () => {
                postImageInput.value = '';
                imagePreview.src = '';
                imagePreviewContainer.style.display = 'none';
            });
        }
    }

    // Delegation for Like Buttons
    document.addEventListener('click', (e) => {
        const likeBtn = e.target.closest('.like-btn');
        if (likeBtn) {
            e.preventDefault();
            const url = likeBtn.dataset.url;
            if (!url) return;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                const countSpan = likeBtn.querySelector('.like-count');
                const icon = likeBtn.querySelector('i');

                if (data.liked) {
                    likeBtn.classList.add('liked');
                    icon.classList.remove('fa-regular');
                    icon.classList.add('fa-solid');
                } else {
                    likeBtn.classList.remove('liked');
                    icon.classList.remove('fa-solid');
                    icon.classList.add('fa-regular');
                }
                if (countSpan) {
                    countSpan.textContent = data.likes_count;
                }
            })
            .catch(err => console.error('Error toggling like:', err));
        }
    });

    // Delegation for Follow Buttons
    document.addEventListener('click', (e) => {
        const followBtn = e.target.closest('.btn-follow');
        if (followBtn) {
            e.preventDefault();
            const url = followBtn.dataset.url;
            if (!url) return;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                const followerCountEl = document.getElementById('follower-count');
                const btnText = followBtn.querySelector('span');

                if (data.following) {
                    followBtn.classList.add('following');
                    if (btnText) btnText.textContent = 'Following';
                } else {
                    followBtn.classList.remove('following');
                    if (btnText) btnText.textContent = 'Follow';
                }

                if (followerCountEl && data.followers_count !== undefined) {
                    followerCountEl.textContent = data.followers_count;
                }
            })
            .catch(err => console.error('Error toggling follow:', err));
        }
    });

    // AJAX Comment Submission
    document.addEventListener('submit', (e) => {
        const commentForm = e.target.closest('.ajax-comment-form');
        if (commentForm) {
            e.preventDefault();
            const url = commentForm.action;
            const formData = new FormData(commentForm);

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const postId = commentForm.dataset.postId;
                    const commentsList = document.getElementById(`comments-list-${postId}`) || document.getElementById('comments-list-main');
                    const commentCountEl = document.getElementById(`comment-count-${postId}`) || document.getElementById('comment-count-main');

                    if (commentsList) {
                        const newCommentHtml = `
                            <div class="comment-item" id="comment-${data.comment_id}">
                                <img src="${data.author_avatar}" class="comment-avatar" alt="${data.author}">
                                <div class="comment-bubble">
                                    <div class="comment-header">
                                        <a href="${data.author_url}" class="comment-author">${data.author}</a>
                                        <div>
                                            <span class="comment-time">${data.created_at}</span>
                                            <button class="comment-del-btn ajax-del-comment" data-url="/comment/${data.comment_id}/delete/" title="Delete comment">
                                                <i class="fa-solid fa-trash-can"></i>
                                            </button>
                                        </div>
                                    </div>
                                    <div class="comment-text">${escapeHtml(data.content)}</div>
                                </div>
                            </div>
                        `;
                        commentsList.insertAdjacentHTML('beforeend', newCommentHtml);
                    }

                    if (commentCountEl) {
                        commentCountEl.textContent = data.comments_count;
                    }

                    commentForm.reset();
                }
            })
            .catch(err => console.error('Error adding comment:', err));
        }
    });

    // Delegation for Comment Deletion
    document.addEventListener('click', (e) => {
        const delBtn = e.target.closest('.ajax-del-comment');
        if (delBtn) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this comment?')) return;

            const url = delBtn.dataset.url;
            const commentItem = delBtn.closest('.comment-item');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    if (commentItem) {
                        commentItem.style.opacity = '0';
                        setTimeout(() => commentItem.remove(), 250);
                    }
                    const countElements = document.querySelectorAll('.comments-count-num');
                    countElements.forEach(el => {
                        el.textContent = data.comments_count;
                    });
                }
            })
            .catch(err => console.error('Error deleting comment:', err));
        }
    });

    // Helper for HTML escaping
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

});
