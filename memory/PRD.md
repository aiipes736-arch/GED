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
