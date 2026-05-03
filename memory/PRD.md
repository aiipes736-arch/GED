# MHCGED — PRD

## Problem Statement
Développer une Gestion Électronique des Documents (GED) professionnelle sécurisée pour le Ministère des Hydrocarbures de la République du Congo (Direction des Systèmes d'Information et de la Communication). Nom: MHCGED. Logo: armoiries officielles. Image d'accueil: drapeau + ministère.

## User Personas
- **Administrateur**: gère les agents, tous les documents et dossiers, voit toutes les activités.
- **Agent**: gère ses propres documents et ceux qui lui sont partagés; ne peut pas accéder à la gestion des agents.

## Core Requirements
- Authentification sécurisée (JWT + cookies httpOnly)
- Rôles: admin, agent
- CRUD Documents (upload, download, edit metadata, delete soft, archive/unarchive, share)
- CRUD Dossiers
- CRUD Agents (admin uniquement)
- Archivage automatique des documents > 5 ans (au démarrage backend)
- Recherche avancée (nom, description, filename, tag, dossier)
- Tags personnalisés
- Partage entre agents
- Journal d'activité (audit log)
- Design institutionnel République du Congo (vert #0F4C3A, jaune, rouge)

## Architecture
- FastAPI + MongoDB (motor) + bcrypt + PyJWT
- Emergent Object Storage pour le stockage des fichiers
- React 19 + Shadcn UI + Tailwind + Sonner toasts
- Fonts: Work Sans (headings), IBM Plex Sans (body)

## What's Been Implemented (2026-05-02)
- Backend: auth (login/logout/me), users CRUD (admin), folders CRUD, documents (upload/list/get/download/update/delete/archive/unarchive/share), tags, dashboard stats, activity log, auto-archive on startup, admin seeding
- Frontend: Login, Dashboard, Documents, Folders, Archives, Agents, Activity, Profile, Sidebar navigation
- All backend tests passing (16/16)
- data-testid attributes on interactive elements

## What's Been Implemented (2026-05-03)
- **In-app notifications**: bell icon in header (polling every 30s) with unread badge, dropdown listing notifs, mark-as-read individual + mark-all-read; auto-created on document share + admin password reset
- **Hierarchical sub-folders**: parent_id support in Folders page (tree view with expand/collapse chevrons, "+" to add child folder, parent dropdown excludes descendants to prevent cycles)
- **Admin password reset**: dedicated "Réinitialiser le mot de passe" action in Agents kebab menu, dialog with new password + confirmation, agent receives in-app notification automatically
- **Monthly PDF reports** (admin only): `/reports` page with month/year/agent selectors, live preview of Top 5 documents downloaded + Top active agents; one-click PDF download with institutional header (logo Congo armoiries + Ministère des Hydrocarbures), green/yellow/red color scheme, signature footer with admin name + date Brazzaville
- New backend endpoints: `GET/POST /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`, `POST /api/users/{id}/reset-password`, `GET /api/reports/monthly`, `GET /api/reports/monthly/pdf`
- All tests passing: 38/38 backend + 100% frontend (notifications, folders hierarchy, password reset, monthly reports)
- New dependency: `reportlab==4.5.0` for PDF generation

## What's Been Implemented (2026-05-03 — communication suite)
- **Private messaging** (`/messages`): conversation list, thread view, optional document attachment, unread badges, auto-notification on new message
- **Document discussions**: "Commentaires" action in document kebab opens dialog with thread; commenter notifies the document owner
- **Inbox** (`/inbox`): documents shared with the current user, "Nouveau" badge, mark-as-read + download, separate from main Documents list
- **Broadcast announcements** (`/announcements`): admin-only create dialog with optional expiration; banner on Dashboard; broadcast notification to all active users
- New backend endpoints: `/api/messages*`, `/api/documents/{id}/comments`, `/api/comments/{id}`, `/api/inbox*`, `/api/announcements*`
- Tests: **64/64 backend** (auth + CRUD + folders + notifications + reports + communication) + 100% frontend

## Backlog / Next Tasks
- P1: Prévisualisation documents (PDF viewer inline)
- P1: Pagination côté backend (list_documents / list_folders / list_users / list_activity)
- P1: Multi-select sur table documents (actions groupées: archiver, supprimer)
- P2: Export Excel/CSV des statistiques et du journal d'activité
- P2: Notifications in-app quand un document est partagé avec l'agent
- P2: Récupération mot de passe (email)
- P2: Arborescence de dossiers (sous-dossiers parent_id déjà supporté côté backend, manque l'UI)
- P2: Purge des fichiers soft-deleted de l'object storage (cron)
- P3: Signature électronique des documents
- P3: Dashboard avec graphiques (activité par jour/semaine)

## Test Credentials
- Admin: admin@mhcged.cg / Admin@2026
