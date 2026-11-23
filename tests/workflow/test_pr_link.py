import sys
import unittest

from helpers import OLD_PLAN, REPO, plan_text

sys.path.insert(0, str(REPO / ".claude" / "scripts"))
import pr_link  # noqa: E402


class PrLinkTest(unittest.TestCase):
    def test_repo_path_from_ssh_and_https(self):
        for url in ["git@github.com:acme/app.git", "git@github.com-work:acme/app.git", "https://github.com/acme/app.git",
                    "https://github.com/acme/app"]:
            self.assertEqual(pr_link.repo_path(url), "acme/app", url)
        self.assertIsNone(pr_link.repo_path("https://gitlab.com/acme/app.git"))

    def test_goal(self):
        self.assertEqual(pr_link.goal(plan_text()), "Users log in to see their data.")
        self.assertEqual(pr_link.goal(OLD_PLAN), "")

    def test_link(self):
        self.assertEqual(pr_link.link("acme/app", "main", "feature/x", "Log in & stay"),
                         "https://github.com/acme/app/compare/main...feature/x?expand=1&body=Log%20in%20%26%20stay")
        self.assertEqual(pr_link.link("acme/app", "main", "feature/x", ""),
                         "https://github.com/acme/app/compare/main...feature/x?expand=1")


if __name__ == "__main__":
    unittest.main()
