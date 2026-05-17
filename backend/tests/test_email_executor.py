"""
Tests for email_executor.py - Email execution service.

TDD RED phase: Tests should fail initially until executor is implemented.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# These imports will fail initially
from app.services.email_executor import EmailExecutor, email_executor
from app.services.email_schemas import EmailConfig, EmailContent, EmailPayload, EmailResult


class TestEmailExecutorInit:
    """Test EmailExecutor initialization."""

    def test_executor_initializes_jinja_environment(self):
        """Should initialize Jinja2 SandboxedEnvironment."""
        executor = EmailExecutor()
        assert executor.env is not None
        # Should use SandboxedEnvironment for security
        from jinja2.sandbox import SandboxedEnvironment
        assert isinstance(executor.env, SandboxedEnvironment)

    def test_executor_singleton_exists(self):
        """Should have singleton instance available."""
        assert email_executor is not None
        assert isinstance(email_executor, EmailExecutor)


class TestRenderTemplate:
    """Test template rendering functionality."""

    def test_render_simple_variable(self):
        """Should render {{variable}} syntax."""
        executor = EmailExecutor()
        result = executor.render_template("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"

    def test_render_nested_object_access(self):
        """Should handle {{user.profile.name}} nested access."""
        executor = EmailExecutor()
        context = {"user": {"profile": {"name": "John"}}}
        result = executor.render_template("Hello {{user.profile.name}}!", context)
        assert result == "Hello John!"

    def test_render_for_loop(self):
        """Should support {% for %} loops."""
        executor = EmailExecutor()
        template = "{% for item in items %}{{item}}{% endfor %}"
        result = executor.render_template(template, {"items": ["a", "b", "c"]})
        assert result == "abc"

    def test_render_if_condition(self):
        """Should support {% if %}/{% else %} conditionals."""
        executor = EmailExecutor()
        template = "{% if show %}Yes{% else %}No{% endif %}"
        assert executor.render_template(template, {"show": True}) == "Yes"
        assert executor.render_template(template, {"show": False}) == "No"

    def test_render_undefined_variable_returns_empty(self):
        """Should return empty string for undefined variables."""
        executor = EmailExecutor()
        result = executor.render_template("Hello {{missing}}!", {})
        assert result == "Hello !"

    def test_render_html_escaping(self):
        """Should auto-escape HTML to prevent XSS."""
        executor = EmailExecutor()
        result = executor.render_template("{{content}}", {"content": "<script>alert('xss')</script>"})
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_render_invalid_syntax_raises_error(self):
        """Should raise clear error for invalid template syntax."""
        executor = EmailExecutor()
        with pytest.raises(Exception) as exc_info:
            executor.render_template("{{unclosed", {})
        assert "template" in str(exc_info.value).lower() or "syntax" in str(exc_info.value).lower()


class TestValidateEmailAddresses:
    """Test email address validation."""

    def test_valid_single_email(self):
        """Should accept valid email addresses."""
        executor = EmailExecutor()
        result = executor.validate_email_addresses(["user@example.com"])
        assert result == ["user@example.com"]

    def test_valid_multiple_emails(self):
        """Should accept multiple valid emails."""
        executor = EmailExecutor()
        emails = ["user1@example.com", "user2@test.org"]
        result = executor.validate_email_addresses(emails)
        assert len(result) == 2

    def test_domain_lowercase_normalization(self):
        """Should normalize domain to lowercase."""
        executor = EmailExecutor()
        result = executor.validate_email_addresses(["User@EXAMPLE.COM"])
        assert result == ["User@example.com"]

    def test_invalid_email_filtered(self):
        """Should filter out invalid emails and log warning."""
        executor = EmailExecutor()
        result = executor.validate_email_addresses(["invalid", "valid@example.com"])
        assert result == ["valid@example.com"]

    def test_empty_list_returns_empty(self):
        """Should handle empty email list."""
        executor = EmailExecutor()
        result = executor.validate_email_addresses([])
        assert result == []


class TestSanitizeHtml:
    """Test HTML sanitization."""

    def test_sanitize_removes_dangerous_tags(self):
        """Should remove script tags."""
        executor = EmailExecutor()
        result = executor.sanitize_html("<script>alert('xss')</script><p>Safe</p>")
        assert "<script>" not in result
        assert "<p>" in result

    def test_sanitize_allows_safe_tags(self):
        """Should allow safe HTML tags."""
        executor = EmailExecutor()
        html = "<p>Paragraph with <strong>bold</strong> and <em>italic</em></p>"
        result = executor.sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result
        assert "<em>" in result

    def test_sanitize_allows_table_structure(self):
        """Should allow table elements."""
        executor = EmailExecutor()
        html = "<table><thead><tr><th>Header</th></tr></thead><tbody><tr><td>Cell</td></tr></tbody></table>"
        result = executor.sanitize_html(html)
        assert "<table>" in result
        assert "<th>" in result
        assert "<td>" in result

    def test_sanitize_allows_links_with_href(self):
        """Should allow anchor tags with href."""
        executor = EmailExecutor()
        html = '<a href="https://example.com">Link</a>'
        result = executor.sanitize_html(html)
        # nh3 may add rel="noopener noreferrer" for security
        assert '<a href="https://example.com"' in result
        assert '>Link</a>' in result


class TestSendEmail:
    """Test email sending functionality (mocked)."""

    @patch('app.services.email_executor.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class):
        """Should send email successfully."""
        # Setup mock
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        executor = EmailExecutor()
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_address="sender@example.com",
        )
        content = EmailContent(
            subject="Test Subject",
            body="<p>Test Body</p>",
            format="html"
        )

        result = executor.send_email(
            config=config,
            content=content,
            to=["recipient@example.com"],
            context={}
        )

        assert result.success is True
        assert result.recipients_count == 1
        mock_smtp.send_message.assert_called_once()

    @patch('app.services.email_executor.smtplib.SMTP')
    def test_send_email_creates_multipart_message(self, mock_smtp_class):
        """Should create multipart message with HTML and plain text."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        executor = EmailExecutor()
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_address="sender@example.com",
        )
        content = EmailContent(
            subject="Test",
            body="<h1>HTML Content</h1><p>Paragraph</p>",
            format="html"
        )

        executor.send_email(
            config=config,
            content=content,
            to=["recipient@example.com"],
            context={}
        )

        # Verify send_message was called
        assert mock_smtp.send_message.called

    @patch('app.services.email_executor.smtplib.SMTP')
    def test_send_email_with_cc_and_bcc(self, mock_smtp_class):
        """Should handle cc and bcc recipients."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        executor = EmailExecutor()
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_address="sender@example.com",
        )
        content = EmailContent(subject="Test", body="Body")

        result = executor.send_email(
            config=config,
            content=content,
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            context={}
        )

        assert result.success is True
        assert result.recipients_count == 3

    @patch('app.services.email_executor.smtplib.SMTP')
    def test_send_email_templates_rendered(self, mock_smtp_class):
        """Should render templates before sending."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        executor = EmailExecutor()
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_address="sender@example.com",
        )
        content = EmailContent(
            subject="Hello {{name}}",
            body="<p>Dear {{name}},</p>",
            format="html"
        )

        executor.send_email(
            config=config,
            content=content,
            to=["recipient@example.com"],
            context={"name": "John"}
        )

        # Verify email was sent (templates rendered)
        assert mock_smtp.send_message.called

    @patch('app.services.email_executor.smtplib.SMTP')
    def test_send_email_handles_smtp_error(self, mock_smtp_class):
        """Should return error result on SMTP failure."""
        mock_smtp_class.side_effect = Exception("Connection refused")

        executor = EmailExecutor()
        config = EmailConfig(
            connection_id="conn-123",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            from_address="sender@example.com",
        )
        content = EmailContent(subject="Test", body="Body")

        result = executor.send_email(
            config=config,
            content=content,
            to=["recipient@example.com"],
            context={}
        )

        assert result.success is False
        assert result.error is not None
        assert "Connection refused" in result.error


class TestExecute:
    """Test execute method with DataSource integration."""

    def test_execute_catches_all_exceptions(self):
        """Should catch exceptions and return error result."""
        executor = EmailExecutor()

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        payload = EmailPayload(
            node_id="node-123",
            target={
                "connection_id": "conn-456",
                "to": "recipient@example.com",
            },
            content=EmailContent(subject="Test", body="Body"),
            metadata={"execution_id": "exec-789", "flow_id": "flow-abc", "timestamp": "2026-01-15T10:00:00Z"},
        )

        result = executor.execute(payload, mock_db)

        assert result.success is False
        assert result.error is not None


class TestIntegration:
    """Integration tests with real template rendering."""

    def test_full_template_workflow(self):
        """Should handle complex template with loops and conditionals."""
        executor = EmailExecutor()

        # Note: Use order.products instead of order.items to avoid dict.items() method conflict
        template = """
<h1>Order #{{order.id}}</h1>
<p>Dear {{customer.name}},</p>
{% if order.products %}
<table>
  <tr><th>Item</th><th>Price</th></tr>
  {% for product in order.products %}
  <tr>
    <td>{{product.name}}</td>
    <td>${{product.price}}</td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p>No items in this order.</p>
{% endif %}
<p>Total: <strong>${{order.total}}</strong></p>
""".strip()

        context = {
            "customer": {"name": "John Doe"},
            "order": {
                "id": "12345",
                "products": [
                    {"name": "Widget", "price": "25.00"},
                    {"name": "Gadget", "price": "50.00"},
                ],
                "total": "75.00"
            }
        }

        result = executor.render_template(template, context)

        # Verify structure
        assert "Order #12345" in result
        assert "John Doe" in result
        assert "Widget" in result
        assert "Gadget" in result
        assert "$75.00" in result
        # Verify table structure preserved
        assert "<table>" in result
        assert "</table>" in result

    def test_undefined_nested_variable(self):
        """Should handle undefined nested variables gracefully."""
        executor = EmailExecutor()

        template = "{{user.name}} - {{user.profile.bio}}"
        context = {"user": {"name": "John"}}  # profile.bio is undefined

        result = executor.render_template(template, context)

        assert "John" in result
        # Undefined should be empty, not error
        assert " - " in result
