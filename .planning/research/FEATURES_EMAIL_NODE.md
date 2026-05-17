# Feature Landscape: Email Node with Dynamic Templates

**Domain:** Email Templating for Integration Flows  
**Researched:** 2026-05-16  
**Project Context:** Dashboard Studio v1.7 - Email Node Milestone  
**Research Mode:** Ecosystem + Comparison

## Overview

This research focuses on email templating capabilities needed for the v1.7 Email Node milestone. The existing Dashboard Studio platform has:

- Flow editor with visual canvas and node configuration UI
- DataSource system with SMTP connection support already built
- Expression evaluation in JavaScript nodes
- Deno-based flow execution infrastructure

The Email Node needs to support dynamic templates using `{{expression}}` syntax for both subject and body content, with special emphasis on dynamic table generation from data arrays.

---

## Table Stakes Features (Must-Have for v1)

Features users expect from any email templating system. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Variable Substitution** | Core templating functionality - replacing `{{variable}}` with data values | Low | Standard across all template engines (Handlebars, Mustache, Liquid, Nunjucks). PROJECT.md specifies `{{expression}}` syntax |
| **Nested Object Access** | Data is often hierarchical (e.g., `{{user.name}}`, `{{order.total}}`) | Low | Dot-notation universally supported. Mustache/Handlebars use `{{user.profile.name}}` |
| **HTML Escaping** | Security requirement - prevents XSS when user data contains HTML | Low | Handlebars/Mustache escape by default. Use triple-brace `{{{}}}` for raw HTML |
| **Iteration/Looping** | Required for dynamic tables and lists (e.g., order items) | Medium | All engines support: Handlebars `{{#each}}`, Liquid `{% for %}`, Mustache `{{#section}}` |
| **Conditional Rendering** | Show/hide content based on data values | Medium | Essential for personalization: `{{#if}}`, `{% if %}` patterns |
| **Default/Fallback Values** | Handle missing data gracefully | Low | Handlebars: `{{firstName "default=Customer"}}`, Liquid: `{{ name \| default: "Customer" }}` |
| **Subject Line Templating** | Dynamic email subjects are essential | Low | Same syntax as body, but must handle special characters carefully |
| **Plain Text & HTML Support** | Both formats needed for email clients | Low | HTML version with templating, plain text fallback |

### Template Syntax Examples

Based on PROJECT.md's `{{expression}}` specification, here are the expected patterns:

```html
<!-- Subject -->
Order Confirmation #{{order.id}} - {{order.status}}

<!-- Basic Variable Substitution -->
<p>Hello {{user.firstName}},</p>
<p>Your order #{{order.id}} has been {{order.status}}.</p>

<!-- Nested Objects -->
<p>Shipping to: {{shipping.address.street}}, {{shipping.address.city}}</p>

<!-- HTML Escaping (safe) -->
<p>Comment: {{review.comment}}</p>
<!-- Result: &lt;script&gt;alert('xss')&lt;/script&gt; -->

<!-- Raw HTML (use with caution) -->
<p>Formatted: {{{review.formattedContent}}}</p>

<!-- Default Values -->
<p>Hello {{user.firstName default="Valued Customer"}},</p>
```

### Iteration for Lists

```html
<!-- Order Items List -->
<ul>
{{#each order.items}}
  <li>{{this.name}} - ${{this.price}} x {{this.quantity}}</li>
{{/each}}
</ul>

<!-- With empty state -->
{{#each order.items}}
  <li>{{name}} - ${{price}}</li>
{{else}}
  <li>No items in this order</li>
{{/each}}
```

### Conditionals

```html
{{#if order.isUrgent}}
  <div class="urgent">PRIORITY ORDER</div>
{{/if}}

{{#if user.isPremium}}
  <p>Thank you for being a Premium member!</p>
{{else}}
  <p>Upgrade to Premium for faster shipping.</p>
{{/if}}
```

---

## Differentiators (v2 or Nice-to-Have)

Features that would set the Email Node apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Built-in Table Generation Helper** | Automatic HTML table from array with headers | Medium | Similar to Liquid's `{% tablerow %}`. Reduces template complexity significantly |
| **Date/Number Formatting Helpers** | Format dates, currency, numbers without preprocessing | Medium | SendGrid Handlebars has `{{formatDate}}`, `{{greaterThan}}` helpers |
| **Template Partials/Include** | Reuse common template sections (headers, footers) | Medium | Handlebars partials: `{{> header}}` |
| **Comparison Operators** | `{{#greaterThan}}`, `{{#equals}}`, `{{#lessThan}}` for numeric comparisons | Low-Medium | SendGrid extends Handlebars with these |
| **Logical Operators** | `{{#and}}`, `{{#or}}` for complex conditionals | Medium | Useful for multi-condition checks |
| **Root Context Access** | Access root data from within loops (`{{@root.companyName}}`) | Low | Handlebars `@root`, Liquid `scope` |
| **Whitespace Control** | Trim whitespace around tags for cleaner output | Low | Handlebars `{{~variable~}}`, Liquid `{%- -%}` |
| **Custom Helper Registration** | Allow users to register custom formatting functions | High | Requires JavaScript execution context |
| **Preview/Testing Mode** | Test templates with sample data before sending | Medium | UI feature with test data input |
| **Template Validation** | Syntax checking and error reporting | Medium | Parse templates for syntax errors |
| **MJML Integration** | Responsive email framework support | High | MJML generates email-client-compatible HTML |
| **Multi-part MIME (attachments)** | Attach files to emails | Medium | Requires binary data handling |
| **Inline CSS** | Automatically inline styles for email client compatibility | Medium | Use libraries like Juice |

---

## Deep Dive: Dynamic Table Generation

The PROJECT.md specifically mentions "generación dinámica de contenido complejo (tablas) a partir de arreglos de objetos". This is a critical feature for email reporting and notifications.

### Approach 1: Manual HTML Table with Iteration (Table Stakes)

Users write standard HTML with iteration blocks:

```html
<table border="1" cellpadding="8" cellspacing="0">
  <thead>
    <tr>
      <th>Product</th>
      <th>Qty</th>
      <th>Price</th>
      <th>Total</th>
    </tr>
  </thead>
  <tbody>
    {{#each items}}
    <tr>
      <td>{{name}}</td>
      <td>{{quantity}}</td>
      <td>${{price}}</td>
      <td>${{multiply price quantity}}</td>
    </tr>
    {{/each}}
  </tbody>
</table>
```

**Pros:**
- Full control over styling
- Standard pattern users know
- No custom implementation needed

**Cons:**
- Verbose, error-prone
- Requires HTML table knowledge
- Repetitive for multiple tables

### Approach 2: Built-in Table Helper (Differentiator)

Similar to Liquid's `{% tablerow %}` or custom Handlebars helper:

```html
<!-- Conceptual syntax -->
{{#table items columns="name,quantity,price,total"}}
  {{#header}}
    <th>Product</th>
    <th>Quantity</th>
    <th>Unit Price</th>
    <th>Total</th>
  {{/header}}
  
  {{#row}}
    <td>{{name}}</td>
    <td>{{quantity}}</td>
    <td>${{price}}</td>
    <td>${{total}}</td>
  {{/row}}
{{/table}}
```

Or simpler with column mapping:

```html
{{table data=items 
        columns="name:Product,quantity:Qty,price:Price" 
        format="price:currency"
        class="report-table"
        striped=true}}
```

**Pros:**
- Less boilerplate
- Consistent styling
- Easier for non-HTML users

**Cons:**
- Less flexibility
- Requires implementing custom helpers
- Learning curve for syntax

### Approach 3: Configuration-Based Table (v2 Idea)

Separate table configuration from template:

```json
{
  "tableConfig": {
    "dataSource": "{{report.items}}",
    "columns": [
      {"field": "name", "header": "Product", "width": "40%"},
      {"field": "quantity", "header": "Qty", "align": "center"},
      {"field": "price", "header": "Price", "format": "currency"},
      {"field": "total", "header": "Total", "format": "currency", "computed": "price * quantity"}
    ],
    "striped": true,
    "bordered": true
  }
}
```

Then reference in template:

```html
{{dynamicTable "tableConfig"}}
```

**Pros:**
- Clean separation
- GUI-friendly
- Reusable configurations

**Cons:**
- Complex implementation
- Requires UI for configuration
- Less immediate control

### Recommendation for v1

**Implement Approach 1 (Manual HTML with Iteration)** as the table stakes solution because:

1. It's what Handlebars/Mustache/Liquid all support out of the box
2. Full flexibility for users who know HTML
3. No custom helper development required
4. Aligns with existing expression evaluation infrastructure
5. Industry standard (SendGrid, Postmark templates use this pattern)

**Defer Approach 2 or 3** to v2 as a differentiator feature.

---

## Template Engine Comparison

| Feature | Handlebars | Mustache | Liquid | Nunjucks |
|---------|------------|----------|--------|----------|
| **Syntax** | `{{var}}` | `{{var}}` | `{{var}}` | `{{var}}` |
| **Logic-less** | No | Yes | No | No |
| **Conditionals** | `{{#if}}` | Limited | `{% if %}` | `{% if %}` |
| **Iteration** | `{{#each}}` | `{{#section}}` | `{% for %}` | `{% for %}` |
| **HTML Escaping** | Yes (default) | Yes (default) | Yes | Yes |
| **Raw Output** | `{{{}}}` | `{{&}}` or `{{{}}}` | `{{ raw }}` | `{{ \| safe }}` |
| **Helpers/Filters** | Yes | No | Yes (filters) | Yes |
| **Partials** | Yes | Yes | Yes | Yes |
| **JavaScript** | Native | Native | Ruby/JS ports | Native |
| **Table Helper** | No | No | `{% tablerow %}` | No |

### Recommendation

**Use Handlebars** or a Handlebars-compatible engine because:

1. **SendGrid uses it** - validates the approach for email templating
2. **`{{expression}}` syntax** - matches PROJECT.md specification
3. **Rich ecosystem** - lots of helpers, well-documented
4. **JavaScript-native** - runs in Deno environment easily
5. **Logic + helpers** - balance of power without being too complex
6. **Triple-brace escape** - `{{{raw}}}` is intuitive for HTML content

**Alternative:** Use a lightweight `{{expression}}` evaluator built on the existing JavaScript expression infrastructure, which would be consistent with other nodes.

---

## Email-Specific Considerations

### HTML Email Best Practices

Based on research of MJML and Postmark templates:

1. **Table-based layouts** - Still required for email client compatibility
2. **Inline CSS** - Most email clients don't support `<style>` blocks in `<head>`
3. **600px max width** - Standard email width
4. **Image alt text** - Always include for accessibility
5. **Plain text fallback** - Essential for deliverability

### Template Safety

```html
<!-- UNSAFE - Never allow -->
<script>alert('xss')</script>
<iframe src="malicious.com"></iframe>

<!-- SAFE with escaping -->
{{userInput}} → &lt;script&gt;alert('xss')&lt;/script&gt;

<!-- SAFE raw HTML (user-controlled) -->
{{{trustedHtmlContent}}}
```

### Email Client Compatibility

| Client | CSS Support | Notes |
|--------|-------------|-------|
| Apple Mail | Excellent | Full modern CSS support |
| Gmail | Good | No `<style>` in head, inline only |
| Outlook (Windows) | Poor | Uses Word rendering engine |
| Outlook (Mac) | Good | WebKit-based |
| Mobile clients | Varies | Generally better than desktop |

**Recommendation:** For v1, provide documentation on email-safe HTML. For v2, consider MJML integration for automatic email-safe HTML generation.

---

## Feature Dependencies

```
Email Node
├── DataSource Integration (SMTP) [EXISTING]
├── Subject Templating [NEW]
├── Body Templating [NEW]
│   ├── Variable Substitution
│   ├── Nested Object Access
│   ├── HTML Escaping
│   ├── Iteration ({{#each}})
│   └── Conditionals ({{#if}})
├── Dynamic Table Generation [NEW]
│   └── Requires Iteration support
└── Flow Context Integration [EXISTING]
    └── Expression evaluation infrastructure
```

---

## Anti-Features (Explicitly NOT Building in v1)

Features to avoid:

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Full Template Inheritance** | Too complex for email templates | Use partials/includes if needed in v2 |
| **Async Operations in Templates** | Blocks email sending, unpredictable | Pre-process data before template evaluation |
| **Complex Logic in Templates** | Business logic belongs in flow nodes | Use JavaScript node before Email node |
| **CSS Inlining** | Can be added later, not core | Document inline style requirements for v1 |
| **Attachment Templating** | Increases complexity significantly | Static attachments only for v1 |
| **Multi-language Templates** | Can be handled by flow logic | Use conditional blocks with language flag |
| **External Template Loading** | Security risk, adds complexity | Templates stored in node configuration |
| **Recursive Templates** | Risk of infinite loops | Not needed for email use cases |

---

## Complexity Assessment by Feature

| Feature | Frontend (UI) | Backend (Deno) | Notes |
|---------|---------------|----------------|-------|
| Variable Substitution | Low | Low | String replacement with context |
| Nested Objects | Low | Low | Dot-notation parser |
| HTML Escaping | Low | Low | Standard escaping function |
| Iteration | Low | Medium | Requires loop context management |
| Conditionals | Low | Medium | Boolean evaluation |
| Default Values | Low | Low | Fallback mechanism |
| Subject Templating | Low | Low | Same engine, single line |
| Manual HTML Tables | Low | Low | Just iteration |
| Table Helper | Medium | Medium | Custom helper registration |
| Date/Number Formatting | Low | Medium | Helper functions |
| Preview Mode | Medium | Low | Test data management |
| Template Validation | Low | Medium | Parse without executing |

---

## Real-World Template Examples

### Order Confirmation Email

```html
<!-- Subject: Order {{order.id}} Confirmed - {{order.items.length}} Items -->

<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Thank you for your order, {{customer.firstName}}!</h2>
  
  <p>Order #{{order.id}} - {{order.date}}</p>
  
  <table width="100%" style="border-collapse: collapse;">
    <tr style="background: #f0f0f0;">
      <th align="left">Item</th>
      <th>Qty</th>
      <th align="right">Price</th>
    </tr>
    {{#each order.items}}
    <tr>
      <td>{{name}}</td>
      <td align="center">{{quantity}}</td>
      <td align="right">${{price}}</td>
    </tr>
    {{/each}}
    <tr style="border-top: 2px solid #000;">
      <td colspan="2" align="right"><strong>Total:</strong></td>
      <td align="right"><strong>${{order.total}}</strong></td>
    </tr>
  </table>
  
  {{#if order.requiresSignature}}
  <p style="color: #d9534f;">This order requires a signature upon delivery.</p>
  {{/if}}
  
  <p>Shipping to:<br>
  {{shipping.address.street}}<br>
  {{shipping.address.city}}, {{shipping.address.state}} {{shipping.address.zip}}</p>
</body>
</html>
```

### Daily Report Email

```html
<!-- Subject: Daily Report - {{report.date}} - {{report.records.length}} Records -->

<html>
<body>
  <h2>Daily Sales Report - {{report.date}}</h2>
  
  <p>Total Sales: ${{report.totalSales}}</p>
  <p>Orders: {{report.orderCount}}</p>
  
  {{#if report.topProducts.length}}
  <h3>Top Products</h3>
  <table border="1" cellpadding="5">
    <tr>
      <th>Product</th>
      <th>Units Sold</th>
      <th>Revenue</th>
    </tr>
    {{#each report.topProducts}}
    <tr>
      <td>{{name}}</td>
      <td>{{unitsSold}}</td>
      <td>${{revenue}}</td>
    </tr>
    {{/each}}
  </table>
  {{else}}
  <p>No sales data available for today.</p>
  {{/if}}
</body>
</html>
```

---

## Sources

| Source | Confidence | Relevance |
|--------|------------|-----------|
| [Handlebars.js Documentation](https://handlebarsjs.com/guide/) | HIGH | Syntax and helpers reference |
| [Mustache Manual](https://mustache.github.io/mustache.5.html) | HIGH | Logic-less templating spec |
| [SendGrid Dynamic Templates](https://sendgrid.com/docs/ui/sending-email/using-handlebars/) | HIGH | Email-specific templating patterns |
| [MJML Documentation](https://documentation.mjml.io/) | HIGH | Email framework with table component |
| [Liquid Template Language](https://shopify.github.io/liquid/) | HIGH | Iteration and tablerow reference |
| [Postmark Templates](https://github.com/ActiveCampaign/postmark-templates) | MEDIUM | Real-world email template examples |
| [Nunjucks](https://mozilla.github.io/nunjucks/) | MEDIUM | JavaScript templating engine |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Variable Substitution | HIGH | Universal pattern, well-documented |
| Iteration Patterns | HIGH | Standard across all engines |
| HTML Escaping | HIGH | Standard security practice |
| Table Generation Approaches | MEDIUM | Multiple valid approaches, need decision |
| Handlebars for Email | HIGH | SendGrid validates this approach |
| Complexity Estimates | MEDIUM | Based on similar implementations |
| Deno Integration | MEDIUM | Handlebars runs in Deno, needs verification |
| Email Client Compatibility | MEDIUM | Based on general email best practices |

---

## Recommendations for Roadmap

### v1 (Current Milestone)

**Must Include:**
1. Variable substitution with `{{expression}}` syntax
2. Nested object access via dot notation (`{{user.profile.name}}`)
3. HTML escaping by default, raw output with `{{{}}}`
4. Iteration with `{{#each}}` for arrays
5. Conditionals with `{{#if}}` / `{{else}}`
6. Default values for missing data
7. Both subject and body templating
8. Manual HTML table creation via iteration

**Implementation approach:**
- Use existing expression evaluation infrastructure if it supports `{{#each}}`/`{{#if}}`
- Or integrate Handlebars-light for Deno
- No custom helpers for v1

### v2 (Future Enhancement)

**Consider Adding:**
1. Built-in table helper for simplified table generation
2. Date/number formatting helpers (`{{formatDate}}`, `{{formatCurrency}}`)
3. Comparison helpers (`{{#greaterThan}}`, `{{#equals}}`)
4. Template preview with test data
5. Partial templates for headers/footers
6. MJML integration for responsive emails
7. CSS inlining for email client compatibility

---

## Open Questions for Phase-Specific Research

1. **Expression Engine:** Should we use Handlebars directly or extend the existing expression evaluator to support `{{#each}}` and `{{#if}}`?

2. **HTML Sanitization:** Beyond escaping, should we sanitize HTML to remove potentially dangerous tags (script, iframe)?

3. **Error Handling:** What happens when a template references a non-existent variable? Empty string? Error? Configurable?

4. **Performance:** How large can templates/data be before Deno execution becomes an issue?

5. **Table Styling:** Should we provide default CSS classes for generated tables, or leave styling entirely to users?

6. **Multiple Recipients:** Should templates support per-recipient personalization when sending to multiple addresses?

7. **Template Storage:** Store templates as strings in node config, or support external template management?

---

## MVP Recommendation

**For v1, prioritize:**

1. ✅ **Variable substitution** - Core functionality
2. ✅ **Nested objects** - Essential for real data structures
3. ✅ **HTML escaping** - Security requirement
4. ✅ **Iteration ({{#each}})** - Required for tables/lists
5. ✅ **Conditionals ({{#if}})** - Basic personalization
6. ✅ **Subject templating** - Complete email functionality

**Defer:**
- ❌ Table helper (use manual HTML)
- ❌ Formatting helpers (pre-process in flow)
- ❌ Partials/includes
- ❌ Comparison operators
- ❌ MJML integration

This gives a solid foundation that users can work with immediately, while leaving room for powerful enhancements in v2.
