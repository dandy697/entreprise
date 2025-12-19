# Vercel Web Analytics Integration Guide for Flask

This guide helps you get started with Vercel Web Analytics on your Flask project.

## Prerequisites

- A Vercel account. If you don't have one, you can [sign up for free](https://vercel.com/signup)
- A Vercel project. If you don't have one, you can [create a new project](https://vercel.com/new)
- The Vercel CLI installed. You can install it using:
  ```bash
  # Using pnpm
  pnpm i vercel
  
  # Using yarn
  yarn i vercel
  
  # Using npm
  npm i vercel
  
  # Using bun
  bun i vercel
  ```

## Step 1: Enable Web Analytics in Vercel

1. Go to the [Vercel dashboard](/dashboard)
2. Select your Flask project
3. Click the **Analytics** tab
4. Click **Enable** from the dialog

> **Note:** Enabling Web Analytics will add new routes (scoped at `/_vercel/insights/*`) after your next deployment.

## Step 2: Add Vercel Analytics to Your Flask App

For Flask applications, the recommended approach is to use the HTML implementation. This method is framework-agnostic and works with any backend framework.

### Add the Analytics Script to Your HTML Template

Add the following script tags to the `<head>` section of your main HTML template(s):

```html
<!-- Vercel Web Analytics -->
<script>
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
</script>
<script defer src="/_vercel/insights/script.js"></script>
```

**Example integration in `templates/index.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Flask App</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    
    <!-- Vercel Web Analytics -->
    <script>
        window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    </script>
    <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
    <!-- Your content here -->
</body>
</html>
```

### Multiple Templates

If your Flask app has multiple templates, make sure to add the Vercel Web Analytics script to each template's `<head>` section, or better yet, use a base template that all other templates extend.

**Example with Jinja2 template inheritance:**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Your Flask App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    
    <!-- Vercel Web Analytics -->
    <script>
        window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    </script>
    <script defer src="/_vercel/insights/script.js"></script>
    
    {% block head %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

Then in your other templates:
```html
<!-- templates/page.html -->
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
    <!-- Your page content here -->
{% endblock %}
```

## Step 3: Deploy Your Flask App to Vercel

Deploy your app using the following command:

```bash
vercel deploy
```

Or if you have connected your Git repository:
```bash
git push
```

Vercel will automatically deploy the latest commits to the main branch.

> **Note:** If everything is set up properly, you should see a Fetch/XHR request to `/_vercel/insights/view` in your browser's Network tab when you visit any page.

## Step 4: View Your Analytics Data

1. Once your app is deployed and users have visited your site, go to your [Vercel dashboard](/dashboard)
2. Select your Flask project
3. Click the **Analytics** tab
4. After a few days of visitors, you'll start seeing data in your analytics dashboard

## How It Works

The Vercel Web Analytics implementation for Flask works as follows:

1. **Script Initialization**: The first script creates a global `window.va` function that queues analytics calls
2. **Script Loading**: The second script loads the actual tracking script from `/_vercel/insights/script.js`
3. **Automatic Tracking**: Once loaded, the script automatically tracks:
   - Page views
   - Visitor information
   - Basic web performance metrics
4. **Data Submission**: The tracking data is sent to Vercel's analytics backend via requests to `/_vercel/insights/view`

## Important Notes

- **No Additional Installation Required**: For Flask applications, you don't need to install the `@vercel/analytics` npm package. The HTML implementation works directly
- **No Route Support**: When using the HTML implementation, there is no automatic route tracking. However, basic page view tracking will work
- **Privacy Compliant**: Vercel Web Analytics is compliant with privacy standards and GDPR regulations
- **Multiple Templates**: If you have multiple HTML templates, ensure each one includes the analytics scripts

## Troubleshooting

### Analytics not showing up

1. Verify the scripts are added to your HTML `<head>` section
2. Check that you've enabled Web Analytics in your Vercel dashboard
3. Wait a few minutes for data to start appearing after a page visit
4. Check your browser's Network tab to confirm `/_vercel/insights/script.js` and `/_vercel/insights/view` requests are being made
5. Verify that your Flask app is properly deployed to Vercel

### CORS Issues

If you see CORS errors in the console:
- This is usually not a problem as the analytics script handles this internally
- The `/_vercel/insights/*` routes are managed by Vercel automatically

## Next Steps

Now that you have Vercel Web Analytics set up, you can:

- Learn more about the [Analytics dashboard](/docs/analytics/filtering)
- Explore [privacy and compliance](/docs/analytics/privacy-policy)
- Check [pricing and limits](/docs/analytics/limits-and-pricing)
- Visit the [Troubleshooting guide](/docs/analytics/troubleshooting) if you need help

For more information, visit the [Vercel Web Analytics documentation](/docs/analytics).
