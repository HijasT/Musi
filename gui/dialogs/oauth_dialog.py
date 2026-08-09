"""Spotify OAuth dialog for authentication."""

import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from threading import Thread
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QProgressBar, QMessageBox,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Signal, QThread

from spotify_api.auth import SpotifyPKCEAuth, extract_code_from_redirect_url, PKCEPair


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def log_message(self, format, *args):
        """Suppress logging."""
        pass

    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        html = """
        <html>
        <head>
            <title>Chaos Media Downloader - Spotify Auth</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                }
                h1 { color: #1db954; }
                p { color: #a0a0a0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to Chaos Media Downloader.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

        # Store the full path for code extraction
        self.server.callback_path = self.path


class CallbackServerThread(QThread):
    """Thread for running the OAuth callback server."""

    callback_received = Signal(str)  # Emits the callback URL path
    server_error = Signal(str)  # Emits error message

    def __init__(self, port: int = 8888, parent=None):
        super().__init__(parent)
        self.port = port
        self.server = None
        self._running = True

    def run(self):
        """Run the callback server."""
        try:
            self.server = HTTPServer(("127.0.0.1", self.port), CallbackHandler)
            self.server.callback_path = None
            self.server.timeout = 1

            while self._running:
                self.server.handle_request()
                if self.server.callback_path:
                    self.callback_received.emit(
                        f"http://127.0.0.1:{self.port}{self.server.callback_path}"
                    )
                    break

        except OSError as e:
            self.server_error.emit(f"Could not start callback server: {e}")
        finally:
            if self.server:
                self.server.server_close()

    def stop(self):
        """Stop the callback server."""
        self._running = False


class SpotifyOAuthDialog(QDialog):
    """Dialog for Spotify OAuth authentication."""

    auth_completed = Signal(bool, str)  # success, message

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.auth = SpotifyPKCEAuth(config)
        self.callback_thread = None
        self.pkce_pair: Optional[PKCEPair] = None
        self.state: Optional[str] = None

        self.setWindowTitle("Connect to Spotify")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("Connect your Spotify Account")
        title.setObjectName("section")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Click the button below to open Spotify in your browser.\n"
            "After logging in, you'll be redirected back here automatically."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Start button
        self.start_btn = QPushButton("Open Spotify Login")
        self.start_btn.clicked.connect(self._start_oauth)
        layout.addWidget(self.start_btn)

        # Progress indicator
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Manual entry fallback
        manual_group = QGroupBox("Manual Entry (if redirect doesn't work)")
        manual_layout = QFormLayout(manual_group)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste the full redirect URL here...")
        manual_layout.addRow("Redirect URL:", self.url_input)

        submit_btn = QPushButton("Submit")
        submit_btn.setObjectName("secondary")
        submit_btn.clicked.connect(self._submit_manual_url)
        manual_layout.addRow("", submit_btn)

        layout.addWidget(manual_group)

        # Cancel button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _start_oauth(self):
        """Start the OAuth flow."""
        try:
            # Begin OAuth flow
            flow = self.auth.begin_oauth_flow(show_dialog=True)
            self.pkce_pair = flow["pkce_pair"]
            self.state = flow["state"]
            auth_url = flow["auth_url"]

            # Get port from redirect URI
            redirect_uri = self.config.get("spotify_redirect_uri", "http://127.0.0.1:8888/callback")
            port = 8888
            try:
                from urllib.parse import urlparse
                parsed = urlparse(redirect_uri)
                if parsed.port:
                    port = parsed.port
            except Exception:
                pass

            # Start callback server
            self.callback_thread = CallbackServerThread(port)
            self.callback_thread.callback_received.connect(self._on_callback_received)
            self.callback_thread.server_error.connect(self._on_server_error)
            self.callback_thread.start()

            # Open browser
            webbrowser.open(auth_url)

            # Update UI
            self.start_btn.setEnabled(False)
            self.progress.show()
            self.status_label.setText("Waiting for Spotify login...\nA browser window should have opened.")

        except Exception as e:
            self.status_label.setText(f"Error starting OAuth: {e}")
            self.status_label.setStyleSheet("color: #e74c3c;")

    def _on_callback_received(self, callback_url: str):
        """Handle OAuth callback received."""
        self._process_callback_url(callback_url)

    def _on_server_error(self, error: str):
        """Handle callback server error."""
        self.progress.hide()
        self.start_btn.setEnabled(True)
        self.status_label.setText(f"Server error: {error}\n\nYou can paste the redirect URL manually below.")
        self.status_label.setStyleSheet("color: #f39c12;")

    def _submit_manual_url(self):
        """Handle manual URL submission."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Empty URL", "Please paste the redirect URL.")
            return
        self._process_callback_url(url)

    def _process_callback_url(self, callback_url: str):
        """Process the OAuth callback URL."""
        try:
            # Extract code from URL
            params = extract_code_from_redirect_url(callback_url)

            if params.get("error"):
                raise RuntimeError(f"Spotify returned error: {params['error']}")

            code = params.get("code")
            if not code:
                raise RuntimeError("No authorization code found in redirect URL")

            # Verify state
            returned_state = params.get("state")
            if self.state and returned_state != self.state:
                raise RuntimeError("State mismatch - possible CSRF attack")

            # Exchange code for token
            self.status_label.setText("Exchanging code for access token...")

            if not self.pkce_pair:
                raise RuntimeError("PKCE pair not found - please restart the login process")

            token = self.auth.exchange_code_for_token(
                code=code,
                code_verifier=self.pkce_pair.code_verifier
            )

            # Success!
            self.progress.hide()
            self.status_label.setText("Successfully connected to Spotify!")
            self.status_label.setStyleSheet("color: #1db954;")
            self.auth_completed.emit(True, "Successfully connected to Spotify")

            # Close dialog after brief delay
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, self.accept)

        except Exception as e:
            self.progress.hide()
            self.start_btn.setEnabled(True)
            self.status_label.setText(f"Authentication failed: {e}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            self.auth_completed.emit(False, str(e))

    def closeEvent(self, event):
        """Handle dialog close."""
        if self.callback_thread and self.callback_thread.isRunning():
            self.callback_thread.stop()
            self.callback_thread.wait(2000)
        super().closeEvent(event)
