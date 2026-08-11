from app.llm.profile_context import build_profile_context


def test_empty_data_still_produces_context():
    # worst case, basically nothing passed in, shouldn't blow up
    context = build_profile_context({})
    assert "@Unknown" in context
    assert "Overall Grade: N/A" in context
    assert "No public repository metadata available." in context


def test_basic_fields_show_up():
    data = {
        "username": "octocat",
        "final_score": 82,
        "grade": "A",
        "breakdown": {
            "activity": 70,
            "impact": 90,
            "skill": 60,
            "language_diversity": 75,
        },
    }
    context = build_profile_context(data)
    assert "@octocat" in context
    assert "Overall Grade: A" in context
    assert "Overall Score: 82 / 100" in context
    assert "Activity Score: 70 / 100" in context
    assert "Impact Score: 90 / 100" in context


def test_repo_with_all_fields():
    data = {
        "repositories": [
            {
                "name": "cool-project",
                "description": "A cool project",
                "language": "Python",
                "stargazers_count": 50,
                "forks_count": 5,
                "open_issues_count": 2,
                "size": 1200,
                "license": "MIT",
                "topics": ["cli", "automation"],
                "fork": False,
            }
        ]
    }
    context = build_profile_context(data)
    assert "Repo Name: cool-project (Owned)" in context
    assert "Description: A cool project" in context
    assert "Primary Language: Python" in context
    assert "Stars: 50 | Forks: 5 | Open Issues: 2" in context
    assert "Size: 1200 KB | License: MIT" in context
    assert "Topics/Tags: cli, automation" in context


def test_forked_repo_labeled_correctly():
    data = {"repositories": [{"name": "forked-one", "fork": True}]}
    context = build_profile_context(data)
    assert "Repo Name: forked-one (Forked)" in context


def test_repo_missing_fields_uses_defaults():
    data = {"repositories": [{"name": "bare-repo"}]}
    context = build_profile_context(data)
    assert "Description: No description provided" in context
    assert "Primary Language: N/A" in context
    assert "Stars: 0 | Forks: 0 | Open Issues: 0" in context
    assert "License: No license" in context
    assert "Topics/Tags: None tagged" in context


def test_stars_prefers_stars_key_over_stargazers_count():
    # some callers might pass already-normalized "stars" instead of raw github key
    data = {"repositories": [{"name": "repo", "stars": 99, "stargazers_count": 5}]}
    context = build_profile_context(data)
    assert "Stars: 99" in context


def test_non_dict_repo_entries_are_skipped():
    data = {"repositories": ["not-a-repo-dict", {"name": "real-repo"}]}
    context = build_profile_context(data)
    assert "real-repo" in context
    assert "not-a-repo-dict" not in context
    # count should still reflect raw list length, since that's counted before filtering
    assert "PUBLIC REPOSITORIES ANALYZED (2 Total)" in context


def test_readme_status_lookup_by_repo_name():
    data = {
        "repositories": [{"name": "documented-repo"}, {"name": "undocumented-repo"}],
        "readme_status": {"documented-repo": True, "undocumented-repo": False},
    }
    context = build_profile_context(data)
    assert "README Documented: YES" in context.split("undocumented-repo")[0]
    assert "README Documented: NO" in context.split("undocumented-repo")[1]


def test_readme_status_falls_back_to_repo_has_readme_flag():
    data = {
        "repositories": [{"name": "repo-with-flag", "has_readme": True}],
        "readme_status": {},
    }
    context = build_profile_context(data)
    assert "README Documented: YES" in context


def test_domain_shares_formatted():
    data = {"skill": {"domain_shares": {"Backend": 75.0, "Frontend": 25.0}}}
    context = build_profile_context(data)
    assert "Domain Distribution: Backend: 75.0%, Frontend: 25.0%" in context


def test_domain_shares_empty_shows_na():
    data = {"skill": {"domain_shares": {}}}
    context = build_profile_context(data)
    assert "Domain Distribution: N/A" in context


def test_language_percentages_formatted():
    data = {"language": {"percentages": {"Python": 80.0, "Go": 20.0}}}
    context = build_profile_context(data)
    assert "Language Breakdown: Python: 80.0%, Go: 20.0%" in context


def test_activity_metrics_included():
    data = {
        "activity": {
            "activity_tier": "Active",
            "total_contributions_365": 300,
            "lifetime_prs": 40,
            "lifetime_issues": 10,
            "collaboration_ratio_365": 16.67,
        }
    }
    context = build_profile_context(data)
    assert "Activity Tier: Active" in context
    assert "Total Contributions (365 days): 300" in context
    assert "Lifetime Pull Requests: 40" in context
    assert "Lifetime Issues Filed: 10" in context
    assert "Collaboration Ratio: 16.67%" in context


def test_license_as_raw_github_dict_is_not_flattened():
    # documents a known gap: real github api returns license as an object,
    # not a plain string, current code just str()'s the whole dict
    data = {
        "repositories": [
            {"name": "repo", "license": {"key": "mit", "name": "MIT License"}}
        ]
    }
    context = build_profile_context(data)
    # this passes today because the dict gets stringified as-is, not because
    # it's the desired output, flag this if the license handling ever gets fixed
    assert "License: {'key': 'mit', 'name': 'MIT License'}" in context
