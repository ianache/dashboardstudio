"""
Tests for email_schemas.py - Email service Pydantic models.

TDD RED phase: Tests should fail initially until schemas are implemented.
"""

import pytest
from pydantic import ValidationError

# This import will fail initially (schemas not created yet)
from app.services.email_schemas import (
    EmailConfig,
    EmailContent,
    EmailPayload,
    EmailResult,
)


class TestEmailContent:
    """Test EmailContent model validation."""

    def test_email_content_required_fields(self):
        """Should require subject and body."""
        with pytest.raises(ValidationError):
            EmailContent()

    def test_email_content_basic_creation(self):
        """Should create with subject and body."""
        content = EmailContent(subject="Hello", body="World")
        assert content.subject == "Hello"
        assert content.body == "World"
        assert content.format == "html"  # default

    def test_email_content_format_validation(self):
        """Should validate format field."""
        # Valid formats
        EmailContent(subject="Test", body="Body", format="html")
        EmailContent(subject="Test", body="Body", format="text")

        # Invalid format should raise
        with pytest.raises(ValidationError):
            EmailContent(subject="Test", body="Body", format="invalid")


class TestEmailPayload:
    """Test EmailPayload model validation."""

    def test_email_payload_required_fields(self):
        """Should require node_id, target, content, metadata."""
        with pytest.raises(ValidationError):
            EmailPayload()

    def test_email_payload_basic_creation(self):
        """Should create with all required fields."""
        payload = EmailPayload(
            node_id="node-123",
            target={
                "connection_id": "conn-456",
                "to": "user@example.com",
            },
            content=EmailContent(subject="Hello", body="World"),
            metadata={
                "execution_id": "exec-789",
                "flow_id": "flow-abc",
                "timestamp": "2026-01-15T10:00:00Z",
            },
        )
        assert payload.node_id == "node-123"
        assert payload.target["connection_id"] == "conn-456"
        assert payload.target["to"] == "user@example.com"

    def test_email_payload_with_cc_bcc(self):
        """Should support cc and bcc recipients."""
        payload = EmailPayload(
            node_id="node-123",
            target={
                "connection_id": "conn-456",
                "to": "user@example.com",
                "cc": "cc@example.com",
                "bcc": "bcc@example.com",
            },
            content=EmailContent(subject="Hello", body="World"),
            metadata={
                "execution_id": "exec-789",
                "flow_id": "flow-abc",
                "timestamp": "2026-01-15T10:00:00Z",
            },
        )
        assert payload.target["cc"] == "cc@example.com"
        assert payload.target["bcc"] == "bcc@example.com"

    def test_email_payload_template_context_default(self):
        """Should default template_context to empty dict."""
        payload = EmailPayload(
            node_id="node-123",
            target={"connection_id": "conn-456", "to": "user@example.com"},
            content=EmailContent(subject="Hello", body="World"),
            metadata={"execution_id": "exec-789", "flow_id": "flow-abc", "timestamp": "2026-01-15T10:00:00Z"},
        )
        assert payload.template_context == {}

    def test_email_payload_with_template_context(self):
        """Should accept template context data."""
        context = {"user": {"name": "John", "email": "john@example.com"}}
        payload = EmailPayload(
            node_id="node-123",
            target={"connection_id": "conn-456", "to": "user@example.com"},
            content=EmailContent(subject="Hello", body="World"),
            metadata={"execution_id": "exec-789", "flow_id": "flow-abc", "timestamp": "2026-01-15T10:00:00Z"},
            template_context=context,
        )
        assert payload.template_context == context


class TestEmailResult:
    """Test EmailResult model validation."""

    def test_email_result_required_fields(self):
        """Should require success field."""
        with pytest.raises(ValidationError):
            EmailResult()

    def test_email_result_basic_creation(self):
        """Should create with success status."""
        result = EmailResult(success=True)
        assert result.success is True
        assert result.message_id is None
        assert result.error is None
        assert result.recipients_count == 0
        assert result.duration_ms == 0

    def test_email_result_full_creation(self):
        """Should create with all fields."""
        result = EmailResult(
            success=True,
            message_id="msg-123",
            error=None,
            recipients_count=3,
            duration_ms=1500,
        )
        assert result.success is True
        assert result.message_id == "msg-123"
        assert result.recipients_count == 3
        assert result.duration_ms == 1500

    def test_email_result_failure_case(self):
        """Should handle failure cases."""
        result = EmailResult(
            success=False,
            error="SMTP connection failed",
            duration_ms=500,
        )
        assert result.success is False
        assert result.error == "SMTP connection failed"


class TestEmailConfig:
    """Test EmailConfig model validation."""

    def test_email_config_required_fields(self):
        """Should require connection_id, smtp_host, smtp_port, smtp_user, smtp_password, from_address."""
        with pytest.raises(ValidationError):
            EmailConfig()

    def test_email_config_basic_creation(self):
        """Should create with all SMTP settings."""
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret123",
            from_address="sender@example.com",
        )
        assert config.connection_id == "conn-123"
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587
        assert config.smtp_use_ssl is True  # default
        assert config.timeout == 30  # default

    def test_email_config_ssl_option(self):
        """Should allow overriding ssl option."""
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=25,
            smtp_use_ssl=False,
            smtp_user="user@example.com",
            smtp_password="secret123",
            from_address="sender@example.com",
        )
        assert config.smtp_use_ssl is False

    def test_email_config_timeout_option(self):
        """Should allow overriding timeout."""
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret123",
            from_address="sender@example.com",
            timeout=60,
        )
        assert config.timeout == 60


class TestModelRelationships:
    """Test relationships between models."""

    def test_payload_contains_content(self):
        """EmailPayload should contain EmailContent."""
        content = EmailContent(subject="Test", body="Body")
        payload = EmailPayload(
            node_id="node-123",
            target={"connection_id": "conn-456", "to": "test@example.com"},
            content=content,
            metadata={"execution_id": "exec-789", "flow_id": "flow-abc", "timestamp": "2026-01-15T10:00:00Z"},
        )
        assert isinstance(payload.content, EmailContent)
        assert payload.content.subject == "Test"

    def test_models_are_pydantic_base_models(self):
        """All models should inherit from Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(EmailContent, BaseModel)
        assert issubclass(EmailPayload, BaseModel)
        assert issubclass(EmailResult, BaseModel)
        assert issubclass(EmailConfig, BaseModel)
