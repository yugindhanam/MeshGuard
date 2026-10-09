"""Exercise actual Streamlit reruns and existing failure controls."""

import unittest
from streamlit.testing.v1 import AppTest


class TestSecurityUI(unittest.TestCase):
    def test_demo_failure_restoration_and_reset(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()
        self.assertFalse(app.exception)
        app.button(key="security_send_all").click().run()
        self.assertFalse(app.exception)
        monitor = app.session_state["security_monitor"]
        self.assertTrue(all(c.delivered == 1 for c in monitor.clients.values()))
        app.button(key="security_attack").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(monitor.clients["Client 2"].status, "RECOVERED")
        self.assertEqual(monitor.clients["Client 1"].status, "NORMAL")
        self.assertEqual(monitor.clients["Client 3"].status, "NORMAL")

        def button(label):
            return next(b for b in app.button if label in b.label)

        button("Find Best Route").click().run()
        next(s for s in app.selectbox if s.label == "Select Active Link to Sever").select("D - F").run()
        button("Sever Link").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["last_healing_event"]["status"], "RECOVERED")
        self.assertEqual(monitor.clients["Client 1"].trust_score, 100)
        app.button(key="security_send_all").click().run()
        self.assertTrue(all(c.last_request == "Database reached" for c in monitor.clients.values()))
        button("Restore Selected Link").click().run()
        self.assertFalse(app.exception)
        next(s for s in app.selectbox if s.label == "Render Engine").select("Static Telemetry Map").run()
        self.assertFalse(app.exception)
        button("Reset Entire Network").click().run()
        self.assertFalse(app.exception)
        monitor = app.session_state["security_monitor"]
        self.assertTrue(all(c.status == "NORMAL" and c.trust_score == 100
                            and c.last_incident is None for c in monitor.clients.values()))
        self.assertEqual(app.session_state["packet_sim"].packets_sent, 0)


if __name__ == "__main__":
    unittest.main()
