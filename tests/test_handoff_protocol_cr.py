from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HandoffProtocolCRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = (ROOT / "HANDOFF_PROTOCOL.md").read_text(encoding="utf-8")
        cls.status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    def test_unambiguous_handoff_and_no_link_rules_remain_mandatory(self):
        self.assertIn("**MERGE NOW — PR #N**", self.protocol)
        self.assertIn("**DO NOT MERGE — PR #N**", self.protocol)
        self.assertIn("Do not provide a PR URL or clickable PR link", self.protocol)
        self.assertIn("The user performs merges", self.protocol)
        self.assertIn("The assistant must not merge", self.protocol)

    def test_local_fallback_requires_explicit_bounded_activation(self):
        required = (
            "local exact-head fallback",
            "project owner has explicitly authorised local validation",
            "known operational reason",
            "checked-out local head must equal the remote PR head",
            "Start and finish with a clean tracked worktree",
            "Execute every command in the ordinary validation workflow",
            "Do not replace a genuinely runner-specific or network-specific gate",
            "any later commit invalidates them",
        )
        for phrase in required:
            self.assertIn(phrase, self.protocol)

    def test_local_fallback_does_not_expand_authority(self):
        self.assertIn("not permission to mutate governed layers", self.protocol)
        self.assertIn("reactivate quarantined work", self.protocol)
        self.assertIn("bypass review", self.protocol)
        self.assertIn("merge automatically", self.protocol)

    def test_first_adoption_cannot_self_authorise(self):
        self.assertIn("cannot silently authorise itself", self.protocol)
        self.assertIn("ADOPT LOCAL VALIDATION FALLBACK — PR #N", self.protocol)
        self.assertIn("does not perform the merge", self.protocol)
        self.assertIn("The user still performs the merge", self.protocol)

    def test_recovery_surface_points_to_the_bounded_fallback(self):
        self.assertIn("Hosted CI remains the normal mode", self.status)
        self.assertIn("local exact-head fallback", self.status)
        self.assertIn("explicit project-owner activation", self.status)
        self.assertIn("full command parity", self.status)


if __name__ == "__main__":
    unittest.main()
