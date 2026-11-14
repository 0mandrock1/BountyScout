import copy
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scout_bounties as sb  # noqa: E402


def iso(days_ago=1):
    t = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def valid():
    return {
        "title": "Fix parser crash",
        "body": "Bounty $200 via https://algora.io/acme/bounties/1",
        "html_url": "https://github.com/acme/repo/issues/1",
        "repository_url": "https://api.github.com/repos/acme/repo",
        "user": {"login": "alice", "type": "User"},
        "labels": [{"name": "bug"}],
        "comments": 2,
        "assignees": [],
        "updated_at": iso(1),
    }


class FilterTests(unittest.TestCase):
    def check(self, **changes):
        item = copy.deepcopy(valid())
        item.update(changes)
        return sb.is_clean_candidate(item)

    def test_valid(self):
        self.assertTrue(sb.is_clean_candidate(valid()))

    def test_pull_request(self):
        self.assertFalse(self.check(pull_request={"url": "x"}))

    def test_assigned(self):
        self.assertFalse(self.check(assignees=[{"login": "bob"}]))
        self.assertFalse(self.check(assignee={"login": "bob"}))

    def test_too_many_comments(self):
        self.assertFalse(self.check(comments=sb.MAX_COMMENTS + 1))

    def test_bot_author(self):
        self.assertFalse(self.check(user={"login": "x", "type": "Bot"}))
        self.assertFalse(self.check(user={"login": "dependabot[bot]", "type": "User"}))

    def test_alert_title(self):
        self.assertFalse(self.check(title="🎯 Bounty Alert: 3 new"))
        self.assertFalse(self.check(title="BOUNTY ALERT: 3 new"))

    def test_owner_deny(self):
        self.assertFalse(self.check(repository_url="https://api.github.com/repos/zhangjiayang6835-cyber/x"))
        self.assertFalse(self.check(user={"login": "zhangjiayang6835-cyber", "type": "User"}))

    def test_junk(self):
        self.assertFalse(self.check(body="Bounty $200 algora.io airdrop for all"))
        self.assertFalse(self.check(body="Bounty $200 algora.io 赏金"))
        self.assertFalse(self.check(body="Bounty $200 algora.io earn coins"))
        self.assertFalse(self.check(body="Bounty $200 algora.io lock it then /claim"))

    def test_offplatform(self):
        self.assertFalse(self.check(body="Bounty $200 algora.io, DM me on telegram"))
        self.assertFalse(self.check(body="Bounty $200 algora.io https://t.me/foo"))

    def test_no_reward(self):
        self.assertFalse(self.check(body="Bounty via https://algora.io/acme"))

    def test_untrusted_platform(self):
        self.assertFalse(self.check(body="Bounty $200 paid by me personally"))

    def test_stale(self):
        self.assertFalse(self.check(updated_at=iso(120)))

    def test_bad_date(self):
        self.assertFalse(self.check(updated_at="not-a-date"))


if __name__ == "__main__":
    unittest.main()
