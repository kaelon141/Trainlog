from src.sql import SqlTemplate

# Feature Requests queries
list_feature_requests = SqlTemplate("src/sql/feature_requests/list_feature_requests.sql")
list_feature_requests_with_votes = SqlTemplate("src/sql/feature_requests/list_feature_requests_with_votes.sql")
insert_feature_request = SqlTemplate("src/sql/feature_requests/insert_feature_request.sql")
update_feature_request_status = SqlTemplate("src/sql/feature_requests/update_feature_request_status.sql")

# Voting queries
insert_vote = SqlTemplate("src/sql/feature_requests/insert_vote.sql")
update_vote = SqlTemplate("src/sql/feature_requests/update_vote.sql")
delete_vote = SqlTemplate("src/sql/feature_requests/delete_vote.sql")
get_user_vote = SqlTemplate("src/sql/feature_requests/get_user_vote.sql")
update_vote_counts = SqlTemplate("src/sql/feature_requests/update_vote_counts.sql")

# Voters list
list_voters = SqlTemplate("src/sql/feature_requests/list_voters.sql")
