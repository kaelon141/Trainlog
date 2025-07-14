import logging
from datetime import datetime

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify

from src.pg import pg_session
from src.sql import feature_requests as fr_sql
from src.utils import getUser, isCurrentTrip, lang, owner_required, owner

logger = logging.getLogger(__name__)

feature_requests_blueprint = Blueprint("feature_requests", __name__)


@feature_requests_blueprint.route("/feature_requests")
def feature_requests(username=None):
    """Display feature requests page, with voting if user is logged in"""
    userinfo = session.get("userinfo", {})
    current_user = userinfo.get("logged_in_user")
    
    with pg_session() as pg:
        if current_user:
            # Get requests with user's votes
            result = pg.execute(
                fr_sql.list_feature_requests_with_votes(),
                {"username": current_user}
            ).fetchall()
        else:
            # Get requests without user votes
            result = pg.execute(fr_sql.list_feature_requests()).fetchall()
        
        # Convert to list of dictionaries
        request_list = []
        for req in result:
            if req[3] == owner:
                author_display='admin'
            else: 
                author_display = req[3]
            request_dict = {
                'id': req[0],
                'title': req[1],
                'description': req[2],
                'author_display': author_display,
                'status': req[4],
                'created': req[5],
                'upvotes': req[6],
                'downvotes': req[7],
                'score': req[8],
                'user_vote': req[9] if len(req) > 9 else 0
            }
            logger.info(f"Feature request: ID={req[0]}, Title={req[1]}")
            request_list.append(request_dict)

    return render_template(
        'feature_requests.html',
        username=current_user,
        requests=request_list,
        **lang.get(userinfo.get("lang", "en"), {}),
        **userinfo,
        nav="bootstrap/navigation.html" if current_user is not "public" else "bootstrap/no_user_nav.html",
        isCurrent=isCurrentTrip(getUser()) if current_user is not "public" else False
    )


def login_required(f):
    """Decorator to require login - implement according to your auth system"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("userinfo", {}).get("logged_in_user"):
            return redirect(url_for("feature_requests"))
        return f(*args, **kwargs)
    return decorated_function


@feature_requests_blueprint.route("/<username>/feature_requests/submit", methods=["POST"])
@login_required
def submit_feature_request(username):
    """Submit a new feature request"""
    title = request.form["title"]
    description = request.form["description"]
    current_user = session["userinfo"]["logged_in_user"]
    
    with pg_session() as pg:
        pg.execute(
            fr_sql.insert_feature_request(),
            {
                "title": title,
                "description": description,
                "username": current_user
            }
        )
    
    return redirect(url_for("feature_requests.feature_requests"))


@feature_requests_blueprint.route("/<username>/feature_requests/edit", methods=["POST"])
@login_required
def edit_feature_request(username):
    """Edit a feature request (owner can edit any, users can edit their own)"""
    request_id = request.form["request_id"]
    title = request.form["title"]
    description = request.form["description"]
    current_user = session["userinfo"]["logged_in_user"]
    is_owner = session["userinfo"].get("is_owner", False)
    
    with pg_session() as pg:
        # Check if user can edit this request
        if not is_owner:
            # Regular user can only edit their own requests
            result = pg.execute(
                fr_sql.get_feature_request_author(),
                {"request_id": request_id}
            ).fetchone()
            
            if not result or result[0] != current_user:
                logger.warning(f"User {current_user} attempted to edit request {request_id} they don't own")
                return redirect(url_for("feature_requests.feature_requests"))
        
        # Update the request
        pg.execute(
            fr_sql.update_feature_request(),
            {
                "request_id": request_id,
                "title": title,
                "description": description
            }
        )
    
    return redirect(url_for("feature_requests.feature_requests"))


@feature_requests_blueprint.route("/<username>/feature_requests/delete", methods=["POST"])
@login_required
def delete_feature_request(username):
    """Delete a feature request (owner can delete any, users can delete their own)"""
    request_id = request.form["request_id"]
    current_user = session["userinfo"]["logged_in_user"]
    is_owner = session["userinfo"].get("is_owner", False)
    
    with pg_session() as pg:
        # Check if user can delete this request
        if not is_owner:
            # Regular user can only delete their own requests
            result = pg.execute(
                fr_sql.get_feature_request_author(),
                {"request_id": request_id}
            ).fetchone()
            
            if not result or result[0] != current_user:
                logger.warning(f"User {current_user} attempted to delete request {request_id} they don't own")
                return redirect(url_for("feature_requests.feature_requests"))
        
        # Delete associated votes first
        pg.execute(
            fr_sql.delete_all_votes_for_request(),
            {"request_id": request_id}
        )
        
        # Delete the request
        pg.execute(
            fr_sql.delete_feature_request(),
            {"request_id": request_id}
        )
    
    return redirect(url_for("feature_requests.feature_requests"))


@feature_requests_blueprint.route("/<username>/feature_requests/vote", methods=["POST"])
@login_required
def vote_feature_request(username):
    """Handle upvote/downvote for feature requests"""
    # Prevent owner from voting
    if session["userinfo"]["is_owner"]:
        return redirect(url_for("feature_requests.feature_requests"))
        
    request_id = request.form.get("request_id")
    vote_type = request.form.get("vote_type")
    current_user = session["userinfo"]["logged_in_user"]
    
    # Validate inputs
    if not request_id or not vote_type:
        logger.error(f"Missing request_id ({request_id}) or vote_type ({vote_type})")
        return redirect(url_for("feature_requests.feature_requests"))
    
    try:
        request_id = int(request_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid request_id: {request_id}")
        return redirect(url_for("feature_requests.feature_requests"))
    
    if vote_type not in ['upvote', 'downvote']:
        logger.error(f"Invalid vote_type: {vote_type}")
        return redirect(url_for("feature_requests.feature_requests"))
    
    with pg_session() as pg:
        # Check if user has already voted on this request
        existing_vote_result = pg.execute(
            fr_sql.get_user_vote(),
            {"request_id": request_id, "username": current_user}
        ).fetchone()
        
        existing_vote = existing_vote_result[0] if existing_vote_result else None
        
        if existing_vote:
            if existing_vote == vote_type:
                # User is clicking the same vote - remove it
                pg.execute(
                    fr_sql.delete_vote(),
                    {"request_id": request_id, "username": current_user}
                )
            else:
                # User is changing their vote
                pg.execute(
                    fr_sql.update_vote(),
                    {
                        "request_id": request_id,
                        "username": current_user,
                        "vote_type": vote_type
                    }
                )
        else:
            # New vote
            pg.execute(
                fr_sql.insert_vote(),
                {
                    "request_id": request_id,
                    "username": current_user,
                    "vote_type": vote_type
                }
            )
        
        # Update vote counts in feature_requests table
        pg.execute(
            fr_sql.update_vote_counts(),
            {"request_id": request_id}
        )
    
    return redirect(url_for("feature_requests.feature_requests"))


@feature_requests_blueprint.route("/<username>/feature_requests/update_status", methods=["POST"])
@owner_required
def update_feature_request_status(username):
    """Update status of a feature request (owner only)"""
    request_id = request.form["request_id"]
    new_status = request.form["status"]
    
    with pg_session() as pg:
        pg.execute(
            fr_sql.update_feature_request_status(),
            {"request_id": request_id, "status": new_status}
        )
    
    return redirect(url_for("feature_requests.feature_requests"))


@feature_requests_blueprint.route("/feature_requests/<int:request_id>/voters")
def feature_request_voters(request_id):
    """Get list of voters for a feature request"""
    with pg_session() as pg:
        result = pg.execute(
            fr_sql.list_voters(),
            {"request_id": request_id}
        ).fetchall()
        
        voters = {
            'upvoters': [],
            'downvoters': []
        }
        
        for vote in result:
            vote_data = {
                'username': vote[0],
                'created': vote[2].isoformat() if vote[2] else None
            }
            
            if vote[1] == 'upvote':
                voters['upvoters'].append(vote_data)
            else:
                voters['downvoters'].append(vote_data)
    
    return jsonify(voters)


@feature_requests_blueprint.route("/feature_requests/<int:request_id>/voters")
def public_feature_request_voters(request_id):
    """Get list of voters for a feature request (public route)"""
    with pg_session() as pg:
        result = pg.execute(
            fr_sql.list_voters(),
            {"request_id": request_id}
        ).fetchall()
        
        voters = {
            'upvoters': [],
            'downvoters': []
        }
        
        for vote in result:
            vote_data = {
                'username': vote[0],
                'created': vote[2].isoformat() if vote[2] else None
            }
            
            if vote[1] == 'upvote':
                voters['upvoters'].append(vote_data)
            else:
                voters['downvoters'].append(vote_data)
    
    return jsonify(voters)


@feature_requests_blueprint.route("/feature_requests/<int:request_id>/details")
def get_feature_request_details(request_id):
    """Get feature request details for editing"""
    with pg_session() as pg:
        result = pg.execute(
            fr_sql.get_feature_request_details(),
            {"request_id": request_id}
        ).fetchone()
        
        if result:
            return jsonify({
                'id': result[0],
                'title': result[1],
                'description': result[2],
                'author': result[3]
            })
        else:
            return jsonify({'error': 'Feature request not found'}), 404