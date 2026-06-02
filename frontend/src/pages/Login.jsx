import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";
import { useSettings } from "../contexts/SettingsContext";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Lock, Mail, Eye, EyeOff, ShieldCheck } from "lucide-react";

export default function Login() {
  const { login, user } = useAuth();
  const { logo_url, hero_url } = useSettings();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (user) navigate("/");
  }, [user, navigate]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await login(email, password);
    setLoading(false);
    if (res.ok) {
      toast.success(`Bienvenue, ${res.user.name || res.user.email}`);
      navigate("/");
    } else {
      toast.error(res.error || "Échec de la connexion");
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left - institutional hero */}
      <div
        className="hidden lg:flex relative w-1/2 bg-cover bg-center"
        style={{ backgroundImage: `url(${hero_url})` }}
      >
        <div className="absolute inset-0 hero-overlay" />
        <div className="relative z-10 flex flex-col justify-between w-full p-12 text-white">
          <div className="flex items-center gap-3">
            <img src={logo_url} alt="MHCGED" className="w-14 h-14 rounded-md border-2 border-white/40" />
            <div>
              <div className="text-xl font-bold tracking-tight" style={{ fontFamily: "Work Sans" }}>
                MHCGED
              </div>
              <div className="text-xs uppercase tracking-[0.25em] text-white/80">
                République du Congo
              </div>
            </div>
          </div>

          <div className="space-y-4 max-w-md">
            <div className="text-[11px] uppercase tracking-[0.35em] text-white/70">
              Ministère des Hydrocarbures
            </div>
            <h1
              className="text-3xl xl:text-4xl font-bold leading-tight"
              style={{ fontFamily: "Work Sans" }}
            >
              Gestion Électronique des Documents
            </h1>
            <p className="text-white/80 text-sm leading-relaxed">
              Plateforme officielle de numérisation, d'archivage et de partage sécurisé
              des documents de la Direction des Systèmes d'Information et de la
              Communication.
            </p>
            <div className="flex items-center gap-2 text-xs text-white/75 pt-2">
              <ShieldCheck size={16} />
              <span>Accès sécurisé — Authentification requise</span>
            </div>
          </div>

          <div className="text-[11px] text-white/60 tracking-wider">
            UNITÉ · TRAVAIL · PROGRÈS
          </div>
        </div>
      </div>

      {/* Right - form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <img src={logo_url} alt="MHCGED" className="w-12 h-12 rounded-md" />
            <div>
              <div className="font-bold text-lg" style={{ fontFamily: "Work Sans" }}>MHCGED</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-gray-500">Ministère des Hydrocarbures</div>
            </div>
          </div>

          <div className="mb-8">
            <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
              Espace sécurisé
            </div>
            <h2
              className="text-3xl font-bold mt-2 text-gray-900"
              style={{ fontFamily: "Work Sans" }}
            >
              Connexion à votre compte
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Veuillez saisir vos identifiants pour accéder à la plateforme.
            </p>
          </div>

          <form onSubmit={onSubmit} className="space-y-5" data-testid="login-form">
            <div>
              <Label htmlFor="email" className="text-gray-700 mb-1.5 inline-block">Adresse e-mail</Label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@mhcged.cg"
                  className="pl-10 h-11"
                  data-testid="login-email"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password" className="text-gray-700 mb-1.5 inline-block">Mot de passe</Label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <Input
                  id="password"
                  type={show ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 pr-10 h-11"
                  data-testid="login-password"
                />
                <button
                  type="button"
                  onClick={() => setShow((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  data-testid="toggle-password"
                >
                  {show ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#0f4c3a] hover:bg-[#1a6b53] text-white font-semibold"
              data-testid="login-submit"
            >
              {loading ? "Connexion..." : "Se connecter"}
            </Button>
          </form>

          <div className="h-1 flag-bar rounded-full mt-10" />
          <p className="text-xs text-gray-400 text-center mt-4">
            © {new Date().getFullYear()} MHCGED — République du Congo
          </p>
        </div>
      </div>
    </div>
  );
}
