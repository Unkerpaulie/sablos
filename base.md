## Overview
I want to build a homepage and projet management system for myself

## Home Page
The home page header will be very simple. No logo, just some links:
 - "Hi" which links to the home page
 - "WIP" (work in progress) which links to the project management system. 
 - "Say Hi" which links to a contact form
 
 The home page will just say something along the lines of "Hi, I'm Paul. I'm an application developer, business consultant, part-time educator, part-time tech tinker. I'm currently building a lot of useful apps. Contact me if you want to learn more or even help out."

The project management system is behind a login page with simple username and password. But this is the main brain of this application. 

## Project Management System

### Data structures
Inside the project management system I need data entities for:
- Clients
- Projects (each belongs to a client)
    - name
    - init prompt (markdown)
    - repo link
    - launch domain
    - launch specs (markdown)
- Objectives (each belongs to project) this is beasically equivalent to a jira issue, but simplified with description, status, priority, due date
- comments (belongs to objective) my own way of adding comments to objectives as I progress through them

### Views
The dashboard should be clean and jusy show current objectives project by project in a table form with truncated description (which I can click on to open project details), status, priority and due date. Sorted by priority then due date. So each project will have a title and then table of objectives below, and these headings should be able to collapse and expand the table below

The side bar should contain the following:
- clients: A list of clients and a button to add new
- projects: list of projects by client. Completed projects included 
- comments: a paginated list of all project comments in descending date order (latest first). This should be searchable

### User interface
Thisshould be simple, based on bootstrap 5, dark/light mode functionality. It can be based on the default botstrap 5 dashboard (https://getbootstrap.com/docs/5.0/examples/dashboard/). The goal is functionality rather than beauty in design

## Tech backend
The entire project will be in django and sqlite3. For now I'll be the only user as the superuser, but I still want the project management system to be behind a secure login because i will lanch this on a server. Eventually I'll add access for non-staff users to have read-only access, but that logic will be a future update
