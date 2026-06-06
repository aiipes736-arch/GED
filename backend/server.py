<!DOCTYPE html>
<html lang="fr" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GED - Ministère des Hydrocarbures - République du Congo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s ease, background-image 0.3s ease;
        }
        /* Custom scrollbar style */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #F4F2EB;
        }
        ::-webkit-scrollbar-thumb {
            background: #C4C2BB;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #A4A29B;
        }
        /* Glass effect utilities */
        .glass-panel {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0, 0, 0, 0.08);
        }
    </style>
</head>
<body class="h-full overflow-hidden bg-[#F4F2EB] text-[#1A1A1A]">

    <div id="app-root" class="h-full w-full flex flex-col">
        <!-- Loader / Splash UI (Hidden once app mounts) -->
        <div id="splash-screen" class="fixed inset-0 z-50 bg-[#F4F2EB] flex flex-col items-center justify-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-800"></div>
            <p class="mt-4 text-sm font-semibold text-emerald-900 tracking-wider">CHARGEMENT DE LA PLATEFORME SECURISEE...</p>
        </div>
    </div>

    <script>
        // Global Application State Store
        const State = {
            currentUser: null, // Initially null to display LoginScreen
            mfaPassed: false,
            activeTab: 'dashboard', // dashboard, documents, messages, history, parameters
            customTitles: {
                main: "Gestion Électronique des Documents",
                ministre: "MINISTÈRE DES HYDROCARBURES",
                pays: "RÉPUBLIQUE DU CONGO"
            },
            wallpaper: {
                type: 'color', // 'color' or 'image'
                value: '#F4F2EB' // Premium Off-White Default
            },
            logo: "https://placehold.co/150x150/104F34/FFFFFF?text=MHC+CONGO", // High-fidelity Fallback Logo
            accounts: [
                { id: 'admin', name: 'Administrateur Principal', email: 'admin@mhcged.cg', role: 'ADMIN', service: 'Sécurité globale' },
                { id: 'dsic', name: 'Ing. Guy-Roger N\'Gassaki', email: 'g.ngassaki@mhcged.cg', role: 'DSIC', service: 'Direction Systèmes d\'Information' },
                { id: 'direction', name: 'Directeur Général Cabinet', email: 'direction@mhcged.cg', role: 'DIRECTION', service: 'Cabinet Ministériel' }
            ],
            localServer: {
                status: 'offline', // online, offline, syncing
                port: '8080',
                ip: '127.0.0.1',
                logs: [
                    '[SYSTÈME] Services prêts à démarrer.',
                    '[DB] Liaison de données chiffrées SQLite locale initialisée.'
                ],
                syncProgress: 0
            },
            documents: [
                { id: 1, name: "Rapport_Forage_Likouala_2026.pdf", size: "4.2 Mo", date: "05/06/2026", category: "Rapports d'Activité", creator: "DSIC", content: "REPUBLIQUE DU CONGO\nMINISTERE DES HYDROCARBURES\n\nRAPPORT TECHNIQUE - EXPLOITATION LIKOUALA\nDate : Juin 2026\n\n1. CONTEXTE DE FORAGE\nLes opérations de forage exploratoire sur le puits de Likouala Est se sont déroulées conformément aux normes géologiques nationales. Les relevés indiquent une colonne sédimentaire hautement favorable avec des réservoirs d'huile compacts.\n\n2. DONNÉES TECHNIQUES COMPLÉMENTAIRES\n- Débit moyen mesuré : 14,500 barils/jour\n- Densité de l'API : 32.4\n- Température moyenne de tête de puits : 87°C\n- Pression interne estimée : 410 bar\n\n3. CONCLUSIONS ET RECOMMANDATIONS\nIl est recommandé d'initier la phase II de production précoce dès approbation finale du cabinet directionnel du Ministère." },
                { id: 2, name: "Decret_Cadre_Hydrocarbures.pdf", size: "1.8 Mo", date: "24/05/2026", category: "Décrets & Réglementations", creator: "Cabinet", content: "REPUBLIQUE DU CONGO\nUNION - TRAVAIL - PROGRES\n\nDECRET PORTANT REGLEMENTATION DES TITRES ET CONCESSIONS PETROLIERES\n\nArticle 1er : Tout titre minier d'hydrocarbures sur le territoire de la République du Congo, qu'il soit offshore ou onshore, est assujetti à la validation d'un plan d'impact socio-environnemental préalable validé par le Ministère en charge.\n\nArticle 2 : Les redevances d'extraction minière sont fixées proportionnellement aux volumes consolidés après arbitrage de l'autorité de régulation pétrolière nationale.\n\nFait à Brazzaville, le 24 Mai 2026." },
                { id: 3, name: "Plan_Strategique_SNH_2026_2030.pdf", size: "12.5 Mo", date: "12/04/2026", category: "Plans Stratégiques", creator: "Direction", content: "MINISTERE DES HYDROCARBURES\nREPUBLIQUE DU CONGO\n\nPLAN STRATÉGIQUE NATIONAL HYDROCARBURES (2026-2030)\n\nAxes Stratégiques Majeurs :\n\n- AXE 1 : Modernisation complète de l'administration des hydrocarbures via la GED (Gestion Électronique des Documents) sécurisée en réseau fermé.\n- AXE 2 : Valorisation et intégration industrielle locale (Local Content) à hauteur de 45% minimum sur l'ensemble de la chaîne de valeur d'ici fin 2028.\n- AXE 3 : Diversification du mix énergétique national avec l'introduction progressive de centrales de co-génération au gaz naturel liquéfié." }
            ],
            messages: [
                { sender: 'Ing. Guy-Roger N\'Gassaki', role: 'DSIC', text: 'La base de données locale du Ministère a été synchronisée. Prêt pour les imports de ce matin.', time: '09:12' },
                { sender: 'Directeur Général Cabinet', role: 'DIRECTION', text: 'Bien reçu. Veuillez téléverser les fiches de synthèse d\'activité pétrolière trimestrielle.', time: '10:04' }
            ],
            systemLogs: [
                { id: 1, action: "Connexion utilisateur sécurisée", user: "DSIC", date: "05/06/2026 19:12:30", ip: "192.168.1.12" },
                { id: 2, action: "Consultation Rapport_Forage_Likouala.pdf", user: "DSIC", date: "05/06/2026 19:15:02", ip: "192.168.1.12" }
            ],
            pdfViewer: {
                isOpen: false,
                document: null,
                zoom: 100
            }
        };

        // Save and Load helper for simple state persistence
        function saveStateToStorage() {
            localStorage.setItem('mhc_ged_state', JSON.stringify({
                customTitles: State.customTitles,
                wallpaper: State.wallpaper,
                logo: State.logo,
                accounts: State.accounts,
                documents: State.documents,
                localServer: {
                    port: State.localServer.port,
                    ip: State.localServer.ip,
                    status: State.localServer.status,
                    logs: State.localServer.logs
                }
            }));
        }

        function loadStateFromStorage() {
            const data = localStorage.getItem('mhc_ged_state');
            if (data) {
                try {
                    const parsed = JSON.parse(data);
                    State.customTitles = parsed.customTitles || State.customTitles;
                    State.wallpaper = parsed.wallpaper || State.wallpaper;
                    State.logo = parsed.logo || State.logo;
                    State.accounts = parsed.accounts || State.accounts;
                    if (parsed.documents) State.documents = parsed.documents;
                    if (parsed.localServer) {
                        State.localServer.port = parsed.localServer.port || State.localServer.port;
                        State.localServer.ip = parsed.localServer.ip || State.localServer.ip;
                        State.localServer.status = parsed.localServer.status || State.localServer.status;
                        State.localServer.logs = parsed.localServer.logs || State.localServer.logs;
                    }
                } catch(e) {
                    console.error("Storage loading fallback initiated.", e);
                }
            }
        }

        loadStateFromStorage();

        // Main Render Function (re-renders active view based on state changes)
        function renderApp() {
            const root = document.getElementById('app-root');
            if (!root) return;

            // Apply global wallpaper layout
            applyGlobalWallpaper();

            if (!State.currentUser) {
                // Show Login Screen
                root.innerHTML = getLoginScreenHTML();
                attachLoginScreenEvents();
            } else if (!State.mfaPassed) {
                // Show MFA verification Screen
                root.innerHTML = getMfaScreenHTML();
                attachMfaScreenEvents();
            } else {
                // Show Dashboard
                root.innerHTML = `
                    <div class="h-full flex flex-col md:flex-row overflow-hidden">
                        <!-- Sidebar Area -->
                        <div class="w-full md:w-80 flex-shrink-0 border-r border-gray-300 flex flex-col glass-panel" style="background-color: #F4F2EB;">
                            ${getSidebarHTML()}
                        </div>
                        
                        <!-- Main Content Workspace Area -->
                        <div class="flex-1 flex flex-col overflow-hidden">
                            ${getHeaderHTML()}
                            <main class="flex-1 overflow-y-auto p-4 md:p-8">
                                ${getMainContentHTML()}
                            </main>
                        </div>
                    </div>
                    ${getPdfViewerModalHTML()}
                `;
                attachDashboardEvents();
                attachPdfViewerEvents();
            }

            // Hide loader screen
            const splash = document.getElementById('splash-screen');
            if (splash) {
                splash.style.display = 'none';
            }
        }

        function applyGlobalWallpaper() {
            const body = document.body;
            if (State.wallpaper.type === 'color') {
                body.style.backgroundImage = 'none';
                body.style.backgroundColor = State.wallpaper.value;
            } else {
                body.style.backgroundImage = `url('${State.wallpaper.value}')`;
                body.style.backgroundSize = 'cover';
                body.style.backgroundPosition = 'center';
                body.style.backgroundRepeat = 'no-repeat';
            }
        }

        // Template HTML for Login Screen
        function getLoginScreenHTML() {
            return `
                <div class="min-h-screen flex items-center justify-center p-4">
                    <div class="max-w-md w-full glass-panel rounded-2xl p-8 shadow-2xl relative overflow-hidden border border-emerald-900/10">
                        <div class="absolute top-0 inset-x-0 h-2 bg-emerald-800"></div>
                        
                        <!-- Country Name & Coat of Arms -->
                        <div class="text-center mb-6">
                            <div class="flex justify-center mb-3">
                                <img src="${State.logo}" alt="Sceau" class="h-20 w-20 rounded-xl shadow-md border-2 border-emerald-800/10 object-cover" id="login-sceau-img">
                            </div>
                            <span class="text-xs font-bold tracking-widest text-emerald-800 uppercase block">${State.customTitles.pays}</span>
                            <h2 class="text-md font-extrabold text-[#1A1A1A] tracking-tight uppercase mt-1 leading-tight">${State.customTitles.ministre}</h2>
                            <p class="text-[11px] text-gray-500 font-medium mt-1">Plateforme GED Sécurisée National</p>
                        </div>

                        <!-- Main Screen Title -->
                        <div class="border-t border-b border-gray-200 py-3 mb-6 text-center">
                            <h1 class="text-xl font-bold text-[#1A1A1A] leading-snug">${State.customTitles.main}</h1>
                        </div>

                        <!-- Direct Profiles Access -->
                        <div class="mb-6">
                            <label class="block text-xs font-bold text-gray-700 uppercase mb-3 text-center">Sélectionner un Profil d'Accès</label>
                            <div class="space-y-3">
                                ${State.accounts.map(acc => `
                                    <button onclick="selectProfileAndConnect('${acc.id}')" class="w-full text-left p-4 rounded-xl border border-gray-200 hover:border-emerald-600 bg-white/70 hover:bg-emerald-50/50 transition-all shadow-sm hover:shadow-md flex items-center justify-between group">
                                        <div>
                                            <div class="font-bold text-sm text-[#1A1A1A]">${acc.name}</div>
                                            <div class="text-xs text-gray-500">${acc.email}</div>
                                            <span class="inline-block mt-1.5 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${acc.role === 'ADMIN' ? 'bg-red-100 text-red-800' : acc.role === 'DIRECTION' ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'}">${acc.role}</span>
                                        </div>
                                        <div class="h-8 w-8 rounded-full bg-emerald-100 group-hover:bg-emerald-800 flex items-center justify-center text-emerald-800 group-hover:text-white transition-colors">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
                                        </div>
                                    </button>
                                `).join('')}
                            </div>
                        </div>

                        <div class="text-center">
                            <p class="text-[10px] text-gray-400 font-semibold tracking-wider">RESEAU SECURISE - MINISTERIE DE L'INNOVATION</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // Template HTML for MFA Strong Authentication Screen
        function getMfaScreenHTML() {
            return `
                <div class="min-h-screen flex items-center justify-center p-4">
                    <div class="max-w-md w-full glass-panel rounded-2xl p-8 shadow-2xl relative border border-emerald-900/10">
                        <div class="absolute top-0 inset-x-0 h-2 bg-emerald-800"></div>

                        <div class="text-center mb-6">
                            <div class="flex justify-center mb-3">
                                <span class="p-3 bg-emerald-100 rounded-full text-emerald-800">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                                </span>
                            </div>
                            <span class="text-xs font-bold tracking-widest text-emerald-800 uppercase block">${State.customTitles.pays}</span>
                            <h2 class="text-sm font-extrabold text-[#1A1A1A] uppercase tracking-tight leading-tight mt-1">${State.customTitles.ministre}</h2>
                        </div>

                        <div class="bg-gray-100/80 p-4 rounded-xl border border-gray-200 mb-6">
                            <p class="text-xs text-gray-600 leading-relaxed text-center">
                                Un jeton de validation temporaire a été envoyé sur l'appareil sécurisé de <br>
                                <strong class="text-[#1A1A1A] block mt-1">${State.currentUser.name}</strong>
                                <span class="text-[10px] font-bold text-emerald-800 block mt-1 tracking-wider">SÉCURISATION PAR JETON PHYSIQUE</span>
                            </p>
                        </div>

                        <div class="mb-6">
                            <label class="block text-xs font-bold text-gray-700 uppercase mb-2 text-center">Saisir le Code d'accès MFA à 4 Chiffres</label>
                            <input type="text" id="mfa-input" placeholder="Ex: 1234" maxlength="4" class="w-full text-center py-3 text-2xl font-bold tracking-widest bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-700 focus:outline-none" autofocus>
                            <p class="text-[11px] text-gray-500 text-center mt-2">Saisir n'importe quelle clé pour simuler la validation (ex: 1234)</p>
                        </div>

                        <div class="space-y-3">
                            <button id="verify-mfa-btn" class="w-full bg-emerald-800 text-white font-bold text-sm py-3 px-4 rounded-xl shadow-md hover:bg-emerald-900 transition-colors uppercase tracking-wider flex items-center justify-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.952 11.952 0 01-7.618 3.0167L3 5.671V11c0 5.523 4.477 10 10 10s10-4.477 10-10V5.671l-1.382-.687z" /></svg>
                                Vérifier la Clé d'Accès
                            </button>
                            <button id="bypass-mfa-btn" class="w-full bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold text-xs py-2 px-4 rounded-xl hover:bg-emerald-200 transition-colors flex items-center justify-center gap-2">
                                ⚡ PASSER L'ÉTAPE MFA
                            </button>
                            <button id="logout-mfa-btn" class="w-full bg-white text-gray-700 border border-gray-300 font-bold text-xs py-2 px-4 rounded-xl hover:bg-gray-50 transition-colors">
                                Retour à l'accueil
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // Template HTML for Sidebar (High Contrast Text and Colors)
        function getSidebarHTML() {
            // Options array to map navigation items
            const menuItems = [
                { id: 'dashboard', label: 'Tableau de Bord', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" /></svg>' },
                { id: 'documents', label: 'Dossiers & Documents', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>', badge: 'GED' },
                { id: 'messages', label: 'Messages Inter-Directions', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>', badge: 'Canal' },
                { id: 'history', label: 'Historique & Audit', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
                { id: 'parameters', label: 'Paramètres de l\'Interface', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>' }
            ];

            return `
                <!-- Ministry Block in Sidebar -->
                <div class="p-6 border-b border-gray-300 flex items-center gap-3">
                    <img src="${State.logo}" alt="Logo" class="h-12 w-12 rounded-lg object-cover shadow-sm border border-emerald-950/20" id="sidebar-logo-img">
                    <div>
                        <h1 class="text-xs font-black text-[#000000] tracking-wider uppercase leading-tight">${State.customTitles.ministre}</h1>
                        <p class="text-[10px] font-bold text-emerald-800 tracking-widest mt-0.5">${State.customTitles.pays}</p>
                    </div>
                </div>

                <!-- Logged In User profile banner -->
                <div class="m-4 p-4 rounded-xl border border-gray-200 bg-white/50 flex flex-col items-center text-center shadow-sm">
                    <div class="h-10 w-10 rounded-full bg-emerald-800 text-white font-black flex items-center justify-center text-sm mb-2 shadow-sm">
                        ${State.currentUser.name.split(' ').map(p => p[0]).join('').substring(0, 2).toUpperCase()}
                    </div>
                    <div class="text-xs font-black text-[#1A1A1A]">${State.currentUser.name}</div>
                    <div class="text-[10px] text-gray-500 font-medium">${State.currentUser.email}</div>
                    <div class="mt-2 flex gap-1 justify-center">
                        <span class="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider bg-emerald-100 text-emerald-800 uppercase border border-emerald-200">
                            ${State.currentUser.role}
                        </span>
                        <span class="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider bg-gray-100 text-gray-700 uppercase border border-gray-200">
                            RH-ACTIVE
                        </span>
                    </div>
                </div>

                <!-- Navigation List - STRICT HIGH CONTRAST (#000000 / #1A1A1A, Bold & Premium) -->
                <div class="flex-1 px-3 space-y-1 overflow-y-auto">
                    ${menuItems.map(item => `
                        <button onclick="switchTab('${item.id}')" 
                                class="w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-150 ${State.activeTab === item.id ? 'bg-emerald-800 text-white shadow-md' : 'text-[#000000] hover:text-[#000000] hover:bg-emerald-800/10'} group">
                            <div class="flex items-center gap-3">
                                <span class="${State.activeTab === item.id ? 'text-white' : 'text-[#1A1A1A] group-hover:text-emerald-800'} transition-colors">
                                    ${item.icon}
                                </span>
                                <span class="text-sm font-bold tracking-tight">${item.label}</span>
                            </div>
                            ${item.badge ? `
                                <span class="text-[10px] font-extrabold px-1.5 py-0.5 rounded-md ${State.activeTab === item.id ? 'bg-white/20 text-white' : 'bg-emerald-800 text-white'} uppercase">
                                    ${item.badge}
                                </span>
                            ` : ''}
                        </button>
                    `).join('')}
                </div>

                <!-- Quick local server controller widget inside sidebar for visibility -->
                <div class="p-4 border-t border-gray-300">
                    <div class="rounded-xl border border-gray-200 bg-white/60 p-3 flex flex-col shadow-sm">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-[10px] font-black text-gray-500 uppercase tracking-wider">SERVEUR LOCAL</span>
                            <div class="flex items-center gap-1.5">
                                <span class="h-2 w-2 rounded-full ${State.localServer.status === 'online' ? 'bg-green-500 animate-pulse' : State.localServer.status === 'syncing' ? 'bg-yellow-500 animate-spin' : 'bg-red-500'}"></span>
                                <span class="text-[10px] font-black uppercase text-gray-700">${State.localServer.status}</span>
                            </div>
                        </div>
                        <button onclick="toggleLocalServer()" class="w-full text-center py-1.5 rounded-lg text-[10px] font-black tracking-wider uppercase border border-gray-300 bg-white hover:bg-gray-50 transition-colors shadow-sm">
                            ${State.localServer.status === 'online' ? '🔴 Éteindre' : '🔌 Démarrer'}
                        </button>
                    </div>
                </div>

                <!-- Footer Section in Sidebar -->
                <div class="p-4 border-t border-gray-300 bg-black/5 flex items-center justify-between">
                    <button onclick="lockScreen()" class="p-2 text-[#1A1A1A] hover:text-emerald-800 hover:bg-white/50 rounded-lg transition-colors flex items-center gap-1 text-xs font-bold">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                        Verrouiller
                    </button>
                    <button onclick="logout()" class="p-2 text-red-700 hover:text-red-900 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-1 text-xs font-bold">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                        Déconnexion
                    </button>
                </div>
            `;
        }

        // Template HTML for Workspace Top Header
        function getHeaderHTML() {
            const today = new Date();
            const formatTime = today.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
            return `
                <header class="h-16 border-b border-gray-300 bg-white/70 backdrop-blur-sm flex items-center justify-between px-6">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-black tracking-widest text-emerald-800 border-r border-gray-300 pr-3 uppercase">BRAZZAVILLE HQ</span>
                        <h2 class="text-sm font-bold text-gray-700 uppercase tracking-tight hidden sm:block">${State.customTitles.main}</h2>
                    </div>
                    <div class="flex items-center gap-4">
                        <!-- Clock and Status indicator -->
                        <div class="flex items-center gap-2 text-xs font-bold text-gray-600 bg-gray-100 px-3 py-1.5 rounded-lg border border-gray-200">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-800" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            <span>${formatTime} | UTC+1</span>
                        </div>
                        <div class="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-800 relative">
                            <span class="absolute top-1 right-1 h-2 w-2 rounded-full bg-emerald-600"></span>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 01-6 0v-1m6 0H9" /></svg>
                        </div>
                    </div>
                </header>
            `;
        }

        // Switch between major sections of app
        function switchTab(tabId) {
            State.activeTab = tabId;
            renderApp();
        }

        // Return HTML based on active tab
        function getMainContentHTML() {
            switch(State.activeTab) {
                case 'dashboard':
                    return getDashboardTabHTML();
                case 'documents':
                    return getDocumentsTabHTML();
                case 'messages':
                    return getMessagesTabHTML();
                case 'history':
                    return getHistoryTabHTML();
                case 'parameters':
                    return getParametersTabHTML();
                default:
                    return getDashboardTabHTML();
            }
        }

        // HTML Template for Dashboard Home Tab
        function getDashboardTabHTML() {
            const rolePrivileges = {
                'ADMIN': 'Accès root complet, journaux d\'audit globaux et paramètres d\'interface.',
                'DSIC': 'Accès développement, gestion des documents techniques, administration système et synchronisation.',
                'DIRECTION': 'Accès Haute Direction, signature électronique de décrets d\'exploitation et visas.'
            };

            return `
                <div class="space-y-6">
                    <!-- Welcome Panel -->
                    <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm relative overflow-hidden">
                        <div class="absolute right-0 bottom-0 opacity-10 pointer-events-none transform translate-y-4">
                            <img src="${State.logo}" alt="Sceau" class="h-44 w-44">
                        </div>
                        <span class="text-[10px] font-black tracking-widest text-emerald-800 uppercase bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-100">ESPACE ADMINISTRATIF CONSOLIDÉ</span>
                        <h2 class="text-2xl font-black text-[#1A1A1A] mt-3">Bonjour, ${State.currentUser.name} !</h2>
                        <p class="text-sm text-gray-600 mt-1.5 leading-relaxed max-w-2xl">
                            Bienvenue sur le portail GED du <strong class="text-emerald-900">${State.customTitles.ministre}</strong>. Vous êtes connecté avec le rôle <strong>${State.currentUser.role}</strong>.
                        </p>
                        <div class="mt-4 p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs font-medium text-gray-700 max-w-xl">
                            💡 <strong class="text-emerald-900">Privilèges actifs :</strong> ${rolePrivileges[State.currentUser.role] || 'Accès standard.'}
                        </div>
                    </div>

                    <!-- Statistics grid row -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <!-- Total Files Card -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-5 shadow-sm flex items-center gap-4">
                            <div class="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-black text-gray-500 uppercase">Documents Archivés</h4>
                                <div class="text-2xl font-black text-[#1A1A1A] mt-0.5">${State.documents.length} fichiers</div>
                                <span class="text-[10px] font-bold text-emerald-700">Stockage cloud chiffré</span>
                            </div>
                        </div>

                        <!-- Messages Card -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-5 shadow-sm flex items-center gap-4">
                            <div class="h-12 w-12 rounded-xl bg-indigo-100 text-indigo-800 flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-black text-gray-500 uppercase">Dépêches Inter-Directions</h4>
                                <div class="text-2xl font-black text-[#1A1A1A] mt-0.5">${State.messages.length} messages</div>
                                <span class="text-[10px] font-bold text-indigo-700">Canal interne crypté</span>
                            </div>
                        </div>

                        <!-- Status Server Card -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-5 shadow-sm flex items-center gap-4">
                            <div class="h-12 w-12 rounded-xl ${State.localServer.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
                            </div>
                            <div>
                                <h4 class="text-xs font-black text-gray-500 uppercase">Base / Serveur Local</h4>
                                <div class="text-xl font-black text-[#1A1A1A] mt-0.5 uppercase">${State.localServer.status === 'online' ? 'OPÉRATIONNEL' : 'ÉTEINT'}</div>
                                <span class="text-[10px] font-bold text-gray-600">IP: ${State.localServer.ip}:${State.localServer.port}</span>
                            </div>
                        </div>
                    </div>

                    <!-- NEW : INTERACTIVE LOCAL SERVER MANAGEMENT COMPONENT -->
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Server Management Card -->
                        <div class="bg-white/95 border border-gray-200 rounded-2xl p-6 shadow-sm lg:col-span-1 space-y-4">
                            <div>
                                <h3 class="text-base font-black text-[#1A1A1A]">Contrôleur de Serveur Local</h3>
                                <p class="text-xs text-gray-500 mt-1">Gérer la liaison locale et l'archivage en miroir physique.</p>
                            </div>

                            <!-- Server status control board -->
                            <div class="p-4 rounded-xl border border-gray-200 bg-gray-50 flex flex-col gap-3">
                                <div class="flex items-center justify-between">
                                    <span class="text-xs font-bold text-gray-700">Statut Réseau :</span>
                                    <span id="server-badge-ui" class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${State.localServer.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                        ${State.localServer.status === 'online' ? 'Actif' : 'Arrêté'}
                                    </span>
                                </div>
                                
                                <div class="space-y-1.5">
                                    <label class="block text-[10px] font-black text-gray-500 uppercase">Port de Communication</label>
                                    <input type="text" id="server-port-input" value="${State.localServer.port}" class="w-full text-xs font-mono p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-800 bg-white" placeholder="Ex: 8080" ${State.localServer.status === 'online' ? 'disabled' : ''}>
                                </div>

                                <div class="space-y-1.5">
                                    <label class="block text-[10px] font-black text-gray-500 uppercase">IP Serveur</label>
                                    <input type="text" id="server-ip-input" value="${State.localServer.ip}" class="w-full text-xs font-mono p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-800 bg-white" placeholder="Ex: 127.0.0.1" ${State.localServer.status === 'online' ? 'disabled' : ''}>
                                </div>
                            </div>

                            <div class="flex gap-2">
                                <button onclick="toggleLocalServer()" class="flex-1 text-center py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider border border-gray-300 shadow-sm transition-colors ${State.localServer.status === 'online' ? 'bg-red-50 text-red-700 hover:bg-red-100 border-red-300' : 'bg-emerald-800 text-white hover:bg-emerald-900 border-emerald-900'}">
                                    ${State.localServer.status === 'online' ? 'Arrêter le Serveur' : 'Lancer le Serveur'}
                                </button>
                                <button onclick="triggerLocalSync()" id="sync-server-btn" class="px-3 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 text-[#1A1A1A] hover:text-emerald-800 transition-colors shadow-sm flex items-center justify-center" ${State.localServer.status === 'offline' ? 'disabled title="Démarrez d\'abord le serveur"' : ''}>
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 15h-.582m0 0H21m-21 0h5.582m0 0h-.582m0 0V9" /></svg>
                                </button>
                            </div>

                            <!-- Sync progress bar -->
                            <div id="sync-progress-container" class="hidden space-y-1">
                                <div class="flex justify-between items-center">
                                    <span class="text-[10px] font-black text-emerald-800 uppercase animate-pulse">Synchronisation miroir en cours...</span>
                                    <span id="sync-percent-label" class="text-[10px] font-bold text-gray-700">0%</span>
                                </div>
                                <div class="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                                    <div id="sync-progress-bar" class="bg-emerald-800 h-full w-0 transition-all duration-150"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Live Terminal Console Logs Card -->
                        <div class="bg-gray-950 border border-gray-800 rounded-2xl p-6 shadow-lg lg:col-span-2 flex flex-col h-64 lg:h-auto">
                            <div class="flex items-center justify-between mb-3 border-b border-gray-800 pb-2">
                                <div class="flex items-center gap-2">
                                    <span class="h-3 w-3 rounded-full bg-red-500"></span>
                                    <span class="h-3 w-3 rounded-full bg-yellow-500"></span>
                                    <span class="h-3 w-3 rounded-full bg-green-500"></span>
                                    <span class="text-xs font-black text-gray-400 font-mono ml-2">CONCENTRATOR_MHC_LOCAL.log</span>
                                </div>
                                <button onclick="clearServerLogs()" class="text-[10px] font-mono text-gray-500 hover:text-gray-300 uppercase tracking-widest">Effacer</button>
                            </div>
                            <div id="terminal-logs" class="flex-1 font-mono text-xs text-green-400 overflow-y-auto space-y-1.5 p-2 bg-black/40 rounded-xl max-h-48 md:max-h-full">
                                ${State.localServer.logs.map(log => `<div class="leading-relaxed opacity-90">${log}</div>`).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Direct Access Quick Links Grid -->
                    <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm">
                        <h3 class="text-base font-black text-[#1A1A1A] mb-4">Raccourcis Directs Système</h3>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <button onclick="switchTab('documents')" class="p-4 rounded-xl border border-gray-200 hover:border-emerald-700 bg-gray-50 hover:bg-emerald-50/20 text-center transition-all">
                                <span class="block text-emerald-800 mb-2 justify-center flex">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                                </span>
                                <span class="text-xs font-bold text-[#1A1A1A]">Nouveau Document</span>
                            </button>
                            <button onclick="switchTab('messages')" class="p-4 rounded-xl border border-gray-200 hover:border-emerald-700 bg-gray-50 hover:bg-emerald-50/20 text-center transition-all">
                                <span class="block text-indigo-800 mb-2 justify-center flex">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                                </span>
                                <span class="text-xs font-bold text-[#1A1A1A]">Envoyer Dépêche</span>
                            </button>
                            <button onclick="switchTab('parameters')" class="p-4 rounded-xl border border-gray-200 hover:border-emerald-700 bg-gray-50 hover:bg-emerald-50/20 text-center transition-all">
                                <span class="block text-amber-700 mb-2 justify-center flex">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                </span>
                                <span class="text-xs font-bold text-[#1A1A1A]">Titres & Visuels</span>
                            </button>
                            <button onclick="switchTab('history')" class="p-4 rounded-xl border border-gray-200 hover:border-emerald-700 bg-gray-50 hover:bg-emerald-50/20 text-center transition-all">
                                <span class="block text-gray-700 mb-2 justify-center flex">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
                                </span>
                                <span class="text-xs font-bold text-[#1A1A1A]">Piste d'Audit</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        // HTML Template for "Dossiers & Documents" Tab
        function getDocumentsTabHTML() {
            return `
                <div class="space-y-6">
                    <!-- Section title -->
                    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div>
                            <h2 class="text-xl font-black text-[#1A1A1A]">Registre des Documents National</h2>
                            <p class="text-xs text-gray-500 mt-1">Consulter, importer ou lire les dossiers de forage et d'exploitation du Ministère.</p>
                        </div>
                        
                        <!-- Upload Input integration -->
                        <div class="flex items-center gap-2">
                            <label class="cursor-pointer bg-emerald-800 text-white font-bold text-xs py-2.5 px-4 rounded-xl hover:bg-emerald-900 transition-all flex items-center gap-2 shadow-sm hover:shadow-md">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                Importer depuis l'ordinateur
                                <input type="file" id="local-file-uploader" class="hidden" accept=".pdf,.doc,.docx" onchange="handleLocalFileUpload(event)">
                            </label>
                        </div>
                    </div>

                    <!-- File search/filter bar -->
                    <div class="bg-white/80 border border-gray-200 rounded-xl p-3 flex flex-col sm:flex-row gap-3">
                        <div class="flex-1 relative">
                            <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 pointer-events-none">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                            </span>
                            <input type="text" placeholder="Rechercher un dossier ministériel..." class="w-full bg-white pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-[#1A1A1A] focus:outline-none focus:ring-1 focus:ring-emerald-800">
                        </div>
                    </div>

                    <!-- Grid of file records -->
                    <div class="bg-white/90 border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
                        <div class="overflow-x-auto">
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="bg-gray-100 border-b border-gray-200">
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase">Intitulé du Fichier</th>
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase">Catégorie</th>
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase">Auteur</th>
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase">Date d'archivage</th>
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase">Taille</th>
                                        <th class="p-4 text-xs font-black text-gray-500 uppercase text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-200 text-xs font-medium">
                                    ${State.documents.map(doc => `
                                        <tr class="hover:bg-gray-50/50 transition-colors">
                                            <td class="p-4 flex items-center gap-2.5">
                                                <span class="text-red-700">
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                                </span>
                                                <div>
                                                    <span class="font-bold text-[#1A1A1A] block">${doc.name}</span>
                                                    <span class="text-[10px] text-gray-400 font-mono">ID: REF-00${doc.id}</span>
                                                </div>
                                            </td>
                                            <td class="p-4 text-gray-600">${doc.category}</td>
                                            <td class="p-4">
                                                <span class="px-2 py-0.5 rounded bg-gray-100 border border-gray-200 text-gray-700 font-bold uppercase tracking-wider text-[10px]">
                                                    ${doc.creator}
                                                </span>
                                            </td>
                                            <td class="p-4 text-gray-500">${doc.date}</td>
                                            <td class="p-4 font-mono text-gray-600">${doc.size}</td>
                                            <td class="p-4 text-right space-x-1">
                                                <button onclick="openPdfViewer(${doc.id})" class="inline-flex items-center gap-1.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 font-bold text-[10px] px-3 py-1.5 rounded-lg border border-emerald-200 uppercase transition-all shadow-sm">
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                                    Visualiser (PDF)
                                                </button>
                                                <button onclick="downloadFakeDocument('${doc.name}')" class="inline-flex items-center gap-1.5 bg-white hover:bg-gray-100 text-gray-700 font-bold text-[10px] px-3 py-1.5 rounded-lg border border-gray-300 uppercase transition-all shadow-sm">
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4-4v12" /></svg>
                                                    Télécharger
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }

        // Simulate a complete and secure local file uploader
        function handleLocalFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Generate size formatted string
            const sizeString = file.size > 1024 * 1024 
                ? (file.size / (1024 * 1024)).toFixed(1) + ' Mo' 
                : (file.size / 1024).toFixed(0) + ' Ko';

            const today = new Date();
            const dateStr = today.toLocaleDateString('fr-FR');

            // Creating the mock document entry
            const newDoc = {
                id: State.documents.length + 1,
                name: file.name,
                size: sizeString,
                date: dateStr,
                category: "Import Externe",
                creator: State.currentUser.role,
                content: `REPUBLIQUE DU CONGO\nMINISTERE DES HYDROCARBURES\n\nDOCUMENT TELEVERSE EN LOCAL\nFichier : ${file.name}\nDate d'importation : ${dateStr} à ${today.toLocaleTimeString('fr-FR')}\n\nCe document a été importé avec succès depuis l'ordinateur par l'utilisateur ${State.currentUser.name} (${State.currentUser.role}).\n\nLe chiffrement AES-256 a été appliqué en local sur les disques de l'administration du Cabinet.`
            };

            // Push and log action in terminal
            State.documents.push(newDoc);
            
            const logEntry = `[GED] Fichier '${file.name}' importé avec succès (${sizeString}). Chiffrement local appliqué.`;
            State.localServer.logs.push(logEntry);
            State.systemLogs.unshift({
                id: State.systemLogs.length + 1,
                action: `Importation locale du document : ${file.name}`,
                user: State.currentUser.role,
                date: `${dateStr} ${today.toLocaleTimeString('fr-FR')}`,
                ip: State.localServer.ip
            });

            saveStateToStorage();
            showLocalNotification(`Le document "${file.name}" a été importé avec succès !`);
            renderApp();
        }

        // HTML Template for "Messages Inter-Directions" Tab
        function getMessagesTabHTML() {
            return `
                <div class="space-y-6">
                    <div>
                        <h2 class="text-xl font-black text-[#1A1A1A]">Dépêches Inter-Directions</h2>
                        <p class="text-xs text-gray-500 mt-1">Canal de transmission ultra-sécurisé du cabinet ministériel.</p>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Left Panel: Department Directory -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-5 shadow-sm space-y-4">
                            <h4 class="text-xs font-black text-[#1A1A1A] uppercase tracking-wider">Membres Actifs du Cabinet</h4>
                            <div class="space-y-2">
                                ${State.accounts.map(acc => `
                                    <div class="p-3 rounded-xl border border-gray-100 bg-gray-50 flex items-center justify-between">
                                        <div>
                                            <div class="text-xs font-black text-[#1A1A1A]">${acc.name}</div>
                                            <div class="text-[10px] text-gray-500">${acc.role} - ${acc.service}</div>
                                        </div>
                                        <span class="h-2.5 w-2.5 rounded-full bg-green-500 border border-white"></span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Right Panel: Message Exchange Sandbox -->
                        <div class="lg:col-span-2 bg-white/90 border border-gray-200 rounded-2xl flex flex-col h-[500px] shadow-sm overflow-hidden">
                            <!-- Exchange Header -->
                            <div class="p-4 border-b border-gray-200 bg-gray-50 flex items-center gap-2">
                                <span class="h-2 w-2 rounded-full bg-emerald-600"></span>
                                <span class="text-xs font-black text-[#1A1A1A] uppercase tracking-wider">Canal Central Crypté</span>
                            </div>

                            <!-- Messages Stream Box -->
                            <div class="flex-1 p-4 overflow-y-auto space-y-4 bg-gray-50/50" id="messages-container">
                                ${State.messages.map(msg => `
                                    <div class="flex flex-col ${msg.role === State.currentUser.role ? 'items-end' : 'items-start'}">
                                        <div class="text-[10px] text-gray-500 font-bold mb-1 flex gap-2 items-center">
                                            <span>${msg.sender} (${msg.role})</span>
                                            <span>•</span>
                                            <span>${msg.time}</span>
                                        </div>
                                        <div class="p-3 rounded-2xl text-xs leading-relaxed max-w-sm shadow-sm border ${msg.role === State.currentUser.role ? 'bg-emerald-800 text-white border-emerald-900 rounded-tr-none' : 'bg-white text-gray-800 border-gray-200 rounded-tl-none'}">
                                            ${msg.text}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>

                            <!-- User Input Area -->
                            <div class="p-4 border-t border-gray-200 bg-white flex gap-2 items-center">
                                <input type="text" id="chat-input" placeholder="Rédiger une dépêche ministérielle..." class="flex-1 bg-gray-100 border border-gray-300 rounded-xl px-4 py-2.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-emerald-800 text-[#1A1A1A]">
                                <button onclick="sendCabinetMessage()" class="bg-emerald-800 hover:bg-emerald-900 text-white font-bold text-xs py-2.5 px-5 rounded-xl transition-colors shadow-sm flex items-center gap-1">
                                    Transmettre
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Append a message to the simulated server log and dashboard chat
        function sendCabinetMessage() {
            const input = document.getElementById('chat-input');
            if (!input || !input.value.trim()) return;

            const text = input.value.trim();
            const now = new Date();
            const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

            const newMsg = {
                sender: State.currentUser.name,
                role: State.currentUser.role,
                text: text,
                time: timeStr
            };

            State.messages.push(newMsg);
            
            // Log this messaging interaction
            State.localServer.logs.push(`[MESSAGERIE] Dépêche cryptée transmise de ${State.currentUser.role}.`);
            saveStateToStorage();
            input.value = '';
            renderApp();

            // Scroll container to bottom
            const container = document.getElementById('messages-container');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }

        // HTML Template for "Historique & Audit" Tab
        function getHistoryTabHTML() {
            return `
                <div class="space-y-6">
                    <div>
                        <h2 class="text-xl font-black text-[#1A1A1A]">Registre d'Audit & Historique</h2>
                        <p class="text-xs text-gray-500 mt-1">Traçabilité complète des accès aux serveurs physiques du Ministère.</p>
                    </div>

                    <div class="bg-white/90 border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
                        <table class="w-full text-left border-collapse text-xs font-medium">
                            <thead>
                                <tr class="bg-gray-100 border-b border-gray-200">
                                    <th class="p-4 text-xs font-black text-gray-500 uppercase">Horodatage précis</th>
                                    <th class="p-4 text-xs font-black text-gray-500 uppercase">Activité / Log</th>
                                    <th class="p-4 text-xs font-black text-gray-500 uppercase">Intervenant</th>
                                    <th class="p-4 text-xs font-black text-gray-500 uppercase">Adresse IP de Session</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                ${State.systemLogs.map(log => `
                                    <tr class="hover:bg-gray-50/50 transition-colors">
                                        <td class="p-4 text-gray-500 font-mono">${log.date}</td>
                                        <td class="p-4 font-bold text-[#1A1A1A]">${log.action}</td>
                                        <td class="p-4">
                                            <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-emerald-100 text-emerald-800">
                                                ${log.user}
                                            </span>
                                        </td>
                                        <td class="p-4 text-gray-600 font-mono">${log.ip}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        // HTML Template for Interface & Title configuration
        function getParametersTabHTML() {
            const activeUserAccounts = State.accounts;
            return `
                <div class="space-y-6">
                    <div>
                        <h2 class="text-xl font-black text-[#1A1A1A]">Paramètres Généraux de l'Interface</h2>
                        <p class="text-xs text-gray-500 mt-1">Personnaliser l'identité visuelle de votre portail GED pour le Ministère.</p>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Column 1: Titles and Customizations -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
                            <h3 class="text-base font-black text-[#1A1A1A]">Configuration des Titres de l'App</h3>
                            
                            <div class="space-y-4">
                                <div class="space-y-1.5">
                                    <label class="block text-xs font-bold text-gray-700 uppercase">Titre Principal de l'Application</label>
                                    <input type="text" id="param-title-main" value="${State.customTitles.main}" class="w-full text-xs font-semibold p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-800 bg-white text-[#1A1A1A]">
                                </div>

                                <div class="space-y-1.5">
                                    <label class="block text-xs font-bold text-gray-700 uppercase">Nom du Ministère officiel</label>
                                    <input type="text" id="param-title-ministre" value="${State.customTitles.ministre}" class="w-full text-xs font-semibold p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-800 bg-white text-[#1A1A1A]">
                                </div>

                                <div class="space-y-1.5">
                                    <label class="block text-xs font-bold text-gray-700 uppercase">Pays / Nation</label>
                                    <input type="text" id="param-title-pays" value="${State.customTitles.pays}" class="w-full text-xs font-semibold p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-800 bg-white text-[#1A1A1A]">
                                </div>
                            </div>

                            <button onclick="saveCustomTitles()" class="w-full bg-emerald-800 hover:bg-emerald-900 text-white font-bold text-xs py-3 px-4 rounded-xl shadow-md transition-colors uppercase tracking-wider">
                                Mettre à jour les titres officiels
                            </button>
                        </div>

                        <!-- Custom Image / Wallpaper selection panel -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
                            <h3 class="text-base font-black text-[#1A1A1A]">Arrière-plan (Wallpaper) de l'Application</h3>
                            <p class="text-xs text-gray-500">Choisir une teinte prédéfinie ou charger une image personnalisée pour le fond d'écran.</p>

                            <div class="space-y-4">
                                <div class="grid grid-cols-3 gap-3">
                                    <!-- Off white preset button -->
                                    <button onclick="setWallpaperColor('#F4F2EB')" class="p-3 rounded-xl border border-gray-200 bg-[#F4F2EB] text-xs font-bold text-gray-800 shadow-sm flex flex-col items-center justify-center hover:scale-105 transition-transform">
                                        <span class="h-5 w-5 rounded-full bg-[#F4F2EB] border border-gray-300 mb-1"></span>
                                        Blanc Cassé
                                    </button>
                                    <!-- Soft light green preset button -->
                                    <button onclick="setWallpaperColor('#E1ECE6')" class="p-3 rounded-xl border border-gray-200 bg-[#E1ECE6] text-xs font-bold text-gray-800 shadow-sm flex flex-col items-center justify-center hover:scale-105 transition-transform">
                                        <span class="h-5 w-5 rounded-full bg-[#E1ECE6] border border-gray-300 mb-1"></span>
                                        Vert Serein
                                    </button>
                                    <!-- Soft cream beige preset button -->
                                    <button onclick="setWallpaperColor('#FAF8F3')" class="p-3 rounded-xl border border-gray-200 bg-[#FAF8F3] text-xs font-bold text-gray-800 shadow-sm flex flex-col items-center justify-center hover:scale-105 transition-transform">
                                        <span class="h-5 w-5 rounded-full bg-[#FAF8F3] border border-gray-300 mb-1"></span>
                                        Beige Sablé
                                    </button>
                                </div>

                                <div class="border-t border-gray-200 pt-4">
                                    <label class="block text-xs font-bold text-gray-700 uppercase mb-2">Importer une image de fond personnalisée</label>
                                    <label class="cursor-pointer block text-center p-4 border-2 border-dashed border-gray-300 hover:border-emerald-700 rounded-xl bg-gray-50 hover:bg-emerald-50/10 transition-colors">
                                        <span class="text-xs font-bold text-[#1A1A1A] block">📁 Téléverser une image (.png, .jpg)</span>
                                        <span class="text-[10px] text-gray-400 mt-0.5 block">Recommandé : 1920x1080px</span>
                                        <input type="file" id="wallpaper-uploader" class="hidden" accept="image/*" onchange="handleWallpaperUpload(event)">
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Column 2: Logo and Accounts modification -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
                            <h3 class="text-base font-black text-[#1A1A1A]">Identité Visuelle (Logo)</h3>
                            <p class="text-xs text-gray-500">Modifier l'armoirie officielle affichée en haut du menu et à la connexion.</p>

                            <div class="flex flex-col sm:flex-row items-center gap-5">
                                <img src="${State.logo}" alt="Sceau Officiel" class="h-20 w-20 rounded-xl border border-gray-200 object-cover shadow-sm" id="params-logo-preview">
                                <div class="flex-1 w-full space-y-2">
                                    <label class="cursor-pointer block text-center py-2.5 px-4 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-xl text-xs font-bold text-gray-800 transition-colors shadow-sm">
                                        Téléverser Sceau Officiel
                                        <input type="file" id="logo-uploader" class="hidden" accept="image/*" onchange="handleLogoUpload(event)">
                                    </label>
                                    <p class="text-[10px] text-gray-400 text-center sm:text-left leading-relaxed">Les modifications sont sauvegardées instantanément dans le cache sécurisé local.</p>
                                </div>
                            </div>
                        </div>

                        <!-- User Profiles Access management -->
                        <div class="bg-white/90 border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
                            <div class="flex items-center justify-between">
                                <h3 class="text-base font-black text-[#1A1A1A]">Gestion des Comptes & Droits</h3>
                                <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800 font-extrabold uppercase tracking-wider">Habilitation</span>
                            </div>

                            <div class="space-y-3">
                                ${activeUserAccounts.map((acc, index) => `
                                    <div class="p-3 rounded-xl border border-gray-100 bg-gray-50 flex flex-col gap-2.5 shadow-sm">
                                        <div class="flex items-center justify-between">
                                            <span class="text-xs font-bold text-[#1A1A1A]">${acc.name}</span>
                                            <span class="text-[10px] font-mono text-gray-400">REF-${index + 1}</span>
                                        </div>
                                        <div class="grid grid-cols-2 gap-2">
                                            <input type="text" value="${acc.name}" onchange="updateAccountInfo(${index}, 'name', this.value)" class="text-[11px] p-2 bg-white border border-gray-300 rounded-lg text-gray-800" placeholder="Nom complet">
                                            <input type="text" value="${acc.email}" onchange="updateAccountInfo(${index}, 'email', this.value)" class="text-[11px] p-2 bg-white border border-gray-300 rounded-lg text-gray-800" placeholder="E-mail">
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Custom logo uploader logic
        function handleLogoUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                State.logo = e.target.result;
                saveStateToStorage();
                showLocalNotification("Logo mis à jour avec succès.");
                renderApp();
            };
            reader.readAsDataURL(file);
        }

        // Custom wallpaper uploader logic
        function handleWallpaperUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                State.wallpaper.type = 'image';
                State.wallpaper.value = e.target.result;
                saveStateToStorage();
                showLocalNotification("Image de fond d'écran configurée.");
                renderApp();
            };
            reader.readAsDataURL(file);
        }

        // Set quick background color
        function setWallpaperColor(colorValue) {
            State.wallpaper.type = 'color';
            State.wallpaper.value = colorValue;
            saveStateToStorage();
            showLocalNotification(`Arrière-plan changé pour la couleur prédéfinie.`);
            renderApp();
        }

        // Update titles dynamic trigger
        function saveCustomTitles() {
            const main = document.getElementById('param-title-main').value;
            const ministre = document.getElementById('param-title-ministre').value;
            const pays = document.getElementById('param-title-pays').value;

            if (main.trim() && ministre.trim() && pays.trim()) {
                State.customTitles.main = main.trim();
                State.customTitles.ministre = ministre.trim().toUpperCase();
                State.customTitles.pays = pays.trim().toUpperCase();

                saveStateToStorage();
                showLocalNotification("Les titres de l'application ont été mis à jour.");
                renderApp();
            }
        }

        // Fast update accounts fields
        function updateAccountInfo(index, field, value) {
            if (State.accounts[index]) {
                State.accounts[index][field] = value.trim();
                saveStateToStorage();
            }
        }

        // Toggle Local Server status
        function toggleLocalServer() {
            const isOnline = State.localServer.status === 'online';
            
            // If turning on, capture IP and port inputs if present
            if (!isOnline) {
                const portInput = document.getElementById('server-port-input');
                const ipInput = document.getElementById('server-ip-input');
                if (portInput && portInput.value.trim()) State.localServer.port = portInput.value.trim();
                if (ipInput && ipInput.value.trim()) State.localServer.ip = ipInput.value.trim();
                
                State.localServer.status = 'online';
                State.localServer.logs.push(`[SYSTEM] Serveur local initialisé sur http://${State.localServer.ip}:${State.localServer.port}`);
                State.localServer.logs.push(`[DB] Base de données PostgreSQL locale synchronisée.`);
            } else {
                State.localServer.status = 'offline';
                State.localServer.logs.push(`[SYSTEM] Fermeture propre des services et déconnexion.`);
            }

            saveStateToStorage();
            renderApp();
            
            // Auto scroll logs console to bottom
            const term = document.getElementById('terminal-logs');
            if (term) term.scrollTop = term.scrollHeight;
        }

        // Simulated Sync process with live loading progress
        function triggerLocalSync() {
            if (State.localServer.status !== 'online') return;

            const progressContainer = document.getElementById('sync-progress-container');
            const progressBar = document.getElementById('sync-progress-bar');
            const percentLabel = document.getElementById('sync-percent-label');
            const syncBtn = document.getElementById('sync-server-btn');

            if (!progressContainer || !progressBar || !percentLabel || !syncBtn) return;

            // Start Sync animation
            syncBtn.disabled = true;
            progressContainer.classList.remove('hidden');
            State.localServer.status = 'syncing';
            
            State.localServer.logs.push(`[SYNC] Lancement de l'archivage miroir sécurisé...`);
            let progress = 0;

            const interval = setInterval(() => {
                progress += Math.floor(Math.random() * 15) + 5;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);

                    // Finalize sync State
                    State.localServer.status = 'online';
                    syncBtn.disabled = false;
                    setTimeout(() => {
                        progressContainer.classList.add('hidden');
                    }, 1000);

                    // Add log entries
                    const syncDateStr = new Date().toLocaleString('fr-FR');
                    State.localServer.logs.push(`[SYNC SUCCESS] Base locale conforme à 100%. (${syncDateStr})`);
                    State.localServer.logs.push(`[ARCHIVE] Transfert des fichiers récents vers le miroir : OK.`);
                    
                    saveStateToStorage();
                    renderApp();
                }

                // Update UI elements smoothly
                progressBar.style.width = `${progress}%`;
                percentLabel.textContent = `${progress}%`;
            }, 250);
        }

        function clearServerLogs() {
            State.localServer.logs = [`[SYSTÈME] Console vidée par l'administrateur.`];
            saveStateToStorage();
            renderApp();
        }

        // HTML Template for Integrated PDF Viewer Modal
        function getPdfViewerModalHTML() {
            if (!State.pdfViewer.isOpen || !State.pdfViewer.document) return '';

            const doc = State.pdfViewer.document;
            return `
                <div class="fixed inset-0 z-50 overflow-hidden bg-black/60 flex items-center justify-center p-4">
                    <div class="bg-zinc-800 text-white rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col shadow-2xl relative">
                        <!-- Top Toolbar of PDF Reader -->
                        <div class="p-4 border-b border-zinc-700 bg-zinc-900 flex flex-wrap items-center justify-between gap-3 rounded-t-2xl">
                            <div class="flex items-center gap-3">
                                <span class="p-2 bg-red-600 rounded text-white font-black text-xs">PDF</span>
                                <div>
                                    <h3 class="text-xs font-bold leading-tight truncate max-w-xs md:max-w-md">${doc.name}</h3>
                                    <p class="text-[10px] text-zinc-400 mt-0.5">Sceau d'Authentification Ministérielle Actif</p>
                                </div>
                            </div>
                            
                            <!-- PDF Zoom & Readout tools -->
                            <div class="flex items-center gap-2 bg-zinc-800 px-3 py-1.5 rounded-lg border border-zinc-700">
                                <button onclick="zoomPdf(-10)" class="text-zinc-400 hover:text-white p-1 transition-colors">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" /></svg>
                                </button>
                                <span class="text-xs font-bold font-mono tracking-wider px-2" id="pdf-zoom-val">${State.pdfViewer.zoom}%</span>
                                <button onclick="zoomPdf(10)" class="text-zinc-400 hover:text-white p-1 transition-colors">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                                </button>
                            </div>

                            <button onclick="closePdfViewer()" class="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                            </button>
                        </div>

                        <!-- Main PDF simulated canvas scrollable area -->
                        <div class="flex-1 overflow-auto p-8 bg-zinc-900/60 flex justify-center">
                            <div class="bg-white text-[#1A1A1A] w-[210mm] min-h-[297mm] p-12 md:p-16 shadow-lg rounded-md origin-top transition-transform relative border border-gray-300" 
                                 style="transform: scale(${State.pdfViewer.zoom / 100});" 
                                 id="pdf-rendered-page">
                                
                                <!-- Official Header Block of simulated document -->
                                <div class="flex items-start justify-between border-b-2 border-emerald-800 pb-4 mb-8">
                                    <div>
                                        <h1 class="text-xs font-black tracking-widest text-emerald-800 uppercase leading-snug">${State.customTitles.pays}</h1>
                                        <p class="text-[9px] font-bold text-gray-500 uppercase tracking-widest mt-0.5">${State.customTitles.ministre}</p>
                                    </div>
                                    <img src="${State.logo}" alt="Sceau" class="h-12 w-12 object-cover">
                                </div>

                                <!-- Watermark watermark stamps of officiality -->
                                <div class="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none select-none">
                                    <img src="${State.logo}" alt="Sceau Filigrane" class="w-80 h-80 object-cover">
                                </div>

                                <!-- Official PDF Document Content -->
                                <div class="whitespace-pre-line text-xs leading-relaxed font-serif text-justify" id="pdf-text-container">
                                    ${doc.content}
                                </div>

                                <!-- Signature block in doc -->
                                <div class="mt-16 border-t border-dashed border-gray-300 pt-6 flex justify-end">
                                    <div class="text-center w-64">
                                        <p class="text-[9px] text-gray-400 font-bold uppercase tracking-wider">Visa Direction Générale</p>
                                        <div class="h-10 my-1 font-mono text-xs text-emerald-800 flex items-center justify-center font-bold tracking-wider italic">
                                            [ APPROUVÉ PAR SÉCURITÉ MFA ]
                                        </div>
                                        <p class="text-[10px] text-emerald-900 font-bold uppercase">${State.currentUser.name}</p>
                                        <p class="text-[8px] text-gray-500 font-medium">Archivé le ${doc.date}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Bottom status info -->
                        <div class="p-3 border-t border-zinc-700 bg-zinc-950 text-[10px] text-zinc-400 font-mono flex items-center justify-between">
                            <span>SÉCURISATION : CLÉ_SHA256_ACTIVE</span>
                            <span>PAGE 1 / 1</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // PDF Visualizer state controls
        function openPdfViewer(documentId) {
            const documentFound = State.documents.find(d => d.id === documentId);
            if (!documentFound) return;

            State.pdfViewer.document = documentFound;
            State.pdfViewer.isOpen = true;
            State.pdfViewer.zoom = 100;

            // Log reading activity
            const todayStr = new Date().toLocaleString('fr-FR');
            State.systemLogs.unshift({
                id: State.systemLogs.length + 1,
                action: `Consultation intégrée du document : ${documentFound.name}`,
                user: State.currentUser.role,
                date: todayStr,
                ip: State.localServer.ip
            });

            saveStateToStorage();
            renderApp();
        }

        function closePdfViewer() {
            State.pdfViewer.isOpen = false;
            State.pdfViewer.document = null;
            renderApp();
        }

        function zoomPdf(val) {
            const newZoom = State.pdfViewer.zoom + val;
            if (newZoom >= 50 && newZoom <= 150) {
                State.pdfViewer.zoom = newZoom;
                const page = document.getElementById('pdf-rendered-page');
                const zoomVal = document.getElementById('pdf-zoom-val');
                if (page) page.style.transform = `scale(${newZoom / 100})`;
                if (zoomVal) zoomVal.textContent = `${newZoom}%`;
            }
        }

        function downloadFakeDocument(docName) {
            showLocalNotification(`Téléchargement de "${docName}" lancé vers votre ordinateur.`);
        }

        // Profile quick select & auto launch MFA validation
        function selectProfileAndConnect(profileId) {
            const account = State.accounts.find(a => a.id === profileId);
            if (!account) return;

            State.currentUser = account;
            State.mfaPassed = false;
            
            saveStateToStorage();
            renderApp();
        }

        function verifyMfaCode() {
            const mfaInput = document.getElementById('mfa-input');
            if (mfaInput) {
                // Accepts any mock verification code for seamless local preview flow
                State.mfaPassed = true;
                
                // Add initial logs entry on successful entry
                const todayStr = new Date().toLocaleString('fr-FR');
                State.localServer.logs.push(`[CONNEXION] Session initiée pour ${State.currentUser.name} (${State.currentUser.role}).`);
                State.systemLogs.unshift({
                    id: State.systemLogs.length + 1,
                    action: "Session authentifiée via clé forte MFA",
                    user: State.currentUser.role,
                    date: todayStr,
                    ip: State.localServer.ip
                });

                saveStateToStorage();
                renderApp();
                showLocalNotification(`Bienvenue, authentification forte réussie !`);
            }
        }

        function bypassMfa() {
            State.mfaPassed = true;
            const todayStr = new Date().toLocaleString('fr-FR');
            State.localServer.logs.push(`[CONNEXION] Session initiée (Contournement MFA) pour ${State.currentUser.name}.`);
            saveStateToStorage();
            renderApp();
        }

        function logout() {
            if (State.currentUser) {
                State.localServer.logs.push(`[DECONNEXION] Session clôturée pour ${State.currentUser.name}.`);
            }
            State.currentUser = null;
            State.mfaPassed = false;
            saveStateToStorage();
            renderApp();
        }

        function lockScreen() {
            State.mfaPassed = false;
            saveStateToStorage();
            renderApp();
        }

        // Attach DOM Events to dynamic elements safely
        function attachLoginScreenEvents() {
            // Unneeded since clicks use inline handlers
        }

        function attachMfaScreenEvents() {
            const verifyBtn = document.getElementById('verify-mfa-btn');
            const bypassBtn = document.getElementById('bypass-mfa-btn');
            const logoutBtn = document.getElementById('logout-mfa-btn');
            const mfaInput = document.getElementById('mfa-input');

            if (verifyBtn) verifyBtn.addEventListener('click', verifyMfaCode);
            if (bypassBtn) bypassBtn.addEventListener('click', bypassMfa);
            if (logoutBtn) logoutBtn.addEventListener('click', logout);
            
            // Allow press Enter to validate
            if (mfaInput) {
                mfaInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') verifyMfaCode();
                });
            }
        }

        function attachDashboardEvents() {
            // Auto scroll of chats if on messages tab
            if (State.activeTab === 'messages') {
                const container = document.getElementById('messages-container');
                if (container) container.scrollTop = container.scrollHeight;
                
                // Press Enter to send message
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    chatInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') sendCabinetMessage();
                    });
                }
            }
        }

        function attachPdfViewerEvents() {
            // Handled inside zoom buttons directly
        }

        // Modern custom notifications (Replacing standard alerts)
        function showLocalNotification(text) {
            // Remove preexisting toast
            const oldToast = document.getElementById('system-toast-notif');
            if (oldToast) oldToast.remove();

            // Create container
            const toast = document.createElement('div');
            toast.id = 'system-toast-notif';
            toast.className = 'fixed bottom-5 right-5 z-50 p-4 bg-emerald-900 text-white rounded-xl shadow-2xl flex items-center gap-3 border border-emerald-800 transition-all transform translate-y-10 opacity-0 max-w-sm';
            toast.innerHTML = `
                <div class="h-6 w-6 rounded-full bg-emerald-800 flex items-center justify-center text-white text-xs">✓</div>
                <div class="text-xs font-bold leading-normal">${text}</div>
            `;

            document.body.appendChild(toast);

            // Animate In
            setTimeout(() => {
                toast.classList.remove('translate-y-10', 'opacity-0');
                toast.classList.add('translate-y-0', 'opacity-100');
            }, 100);

            // Animate Out
            setTimeout(() => {
                toast.classList.add('translate-y-10', 'opacity-0');
                setTimeout(() => toast.remove(), 500);
            }, 4000);
        }

        // Final Mount of App Root
        window.onload = function() {
            setTimeout(() => {
                renderApp();
            }, 1000); // Elegant fake splash delay for load simulation
        }
    </script>
</body>
</html>
