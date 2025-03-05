# KDL Mini Scripts
This is a collection of scripts that KDL uses.

## Address to Library Card Type
[ put more details here ]

## Book Cover Image Fetcher
Fetches book cover image based on the book's ID in the catalog
- Receives an API key and a title_id (of a BiblioCommons book title)
- Uses the BiblioCore API to retrieve the title record and grab the first ISBN
- Returns the Syndetics book cover image for that ISBN

## Write Michigan Reviewer Self-Signup
Allows a volunteer reviewer to enter their email address to join our Submittable Team, and walks them through next steps like creating a Submittable account
- User enters an email address in the text box and submits
- Uses the Submittable API to check that email's status in our team, adding them if needed
- Checks if that email has a Submittable account
- Gives feedback to user about next steps

## Write Michigan Submission Review Tools
This is currently broken and might have caused Submittable to block our Render.com server ¯\\\_(ツ)\_/¯
