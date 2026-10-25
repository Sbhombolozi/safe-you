# safe-you
# Safe YOU

A survivor-support app for people experiencing domestic abuse and gender-based violence. Safe YOU helps a person ask for help quickly and keep a record of what happened that cannot be quietly changed.

Built by team **SBHOMBOLOZI** for the FNB App of the Year Hackathon 2026, in the *Safer communities and gender-based violence response* challenge.

## The problem

- Asking for help can be unsafe when an abuser is nearby or watching.
- Evidence kept in chat apps and photo galleries is easy to lose, delete or dispute.
- Support organisations struggle to see where help is needed without exposing anyone's personal data.

## What the prototype does

- **Evidence journal:** private notes and photos. Every entry is SHA-256 hashed and linked to the previous entry's hash, so any later change can be detected.
- **Panic button:** one press saves an alert with the user's live location and opens a pre-filled WhatsApp message with a map link to their top-priority contact.
- **Trusted contacts:** up to 7 contacts per user, with the limit enforced by the database.
- **Admin insights:** an aggregate-only dashboard (users, panic activity, age group, area type, province). Groups smaller than 5 are hidden, and access is limited to admins.

## Try it

- **Live app: https://studio.flet.dev/run/nRkVwt84tm
- **Demo login: [sbekezelo189704@gmail.com / [testproject@124]
- **Admin demo login:[sbhombolozi@gmail.com / [testproject@123]

## Tech stack

- **Flet (Python):** user interface, built in Flet Studio
- **Supabase:** authentication, PostgreSQL database and private file storage
- **PostgreSQL Row Level Security, functions and triggers:** per-user data access, aggregate-only admin statistics and the 7-contact limit
- **SHA-256 hash chaining:** tamper-evident evidence journal
- **WhatsApp click-to-chat (wa.me):** pre-filled emergency alert

## Project structure

Key files include `views/app_shell.py` (app shell and tabs), `views/panic.py` (panic button), `views/contacts.py` (trusted contacts) and `services/panic_api.py` (saving panic alerts).

## Security and privacy

- Every table is restricted to its owner with Row Level Security.
- The app uses only the Supabase anon key. No service_role key or other secret is stored in this repository.
- Evidence photos are stored in a private bucket with a file-size limit and allowed file types.
- Admin statistics come from a database function that returns aggregates only and hides groups under 5.
- Profile fields such as age group, area type and province are optional.
- Designed with POPIA principles in mind.

## Run locally

[Fill in the steps for your project: install Python and Flet, set your own Supabase URL and anon key in the app's configuration, then run the app with Flet.]

## Roadmap

- Next:automatic SMS alerts through a paid provider, audio and video evidence uploads, and recording on panic after a legal review of consent laws.
- Later:an Android build with a disguised interface, an iOS version with visible recording, and an independent privacy and security review.

## Status

This is a hackathon prototype and is not ready for real-world safety use. If you are in danger, contact your local emergency services.
