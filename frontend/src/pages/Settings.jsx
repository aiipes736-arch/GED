import React, { useState, useRef } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { useSettings } from "../contexts/SettingsContext";
import { Navigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Settings as SettingsIcon, Upload, RefreshCw } from "lucide-react";

function ImageUploader({ label, currentUrl, endpoint, onDone, testIdPrefix }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setPreview(URL.createObjectURL(f));
  };

  const onUpload = async () => {
    const f = inputRef.current?.files?.[0];
    if (!f) {
      toast.error("Veuillez sélectionner une image");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", f);
      await api.post(endpoint, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`${label} mis à jour`);
      setPreview(null);
      inputRef.current.value = "";
      onDone?.();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="inst-card p-5">
      <div className="text-[11px] uppercase tracking-wider text-gray-500 font-semibold mb-3">{label}</div>
      <div className="flex items-start gap-5">
        <div className="w-32 h-32 rounded-md overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center flex-shrink-0">
          {preview ? (
            <img src={preview} alt="Aperçu" className="w-full h-full object-cover" />
          ) : currentUrl ? (
            <img src={currentUrl} alt={label} className="w-full h-full object-cover" data-testid={`${testIdPrefix}-current`} />
          ) : (
            <span className="text-gray-400 text-xs">Aucune image</span>
          )}
        </div>
        <div className="flex-1 space-y-3">
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={onPick}
            className="text-sm"
            data-testid={`${testIdPrefix}-input`}
          />
          <div className="flex gap-2">
            <Button
              onClick={onUpload}
              disabled={uploading}
              className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
              data-testid={`${testIdPrefix}-submit`}
            >
              <Upload size={14} className="mr-1" />
              {uploading ? "Envoi..." : "Téléverser"}
            </Button>
            {preview && (
              <Button variant="outline" onClick={() => { setPreview(null); inputRef.current.value = ""; }}>
                Annuler
              </Button>
            )}
          </div>
          <p className="text-xs text-gray-500">
            Formats acceptés : PNG, JPG, WEBP · Conseillé : ratio 1:1 pour le logo, 16:9 pour l'image d'accueil
          </p>
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const { logo_url, hero_url, refresh } = useSettings();

  if (user && user.role !== "admin") return <Navigate to="/" replace />;

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            Administration
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            Paramètres
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Personnalisez l'identité visuelle de votre plateforme MHCGED
          </p>
        </div>
        <Button variant="outline" onClick={refresh}>
          <RefreshCw size={14} className="mr-2" /> Rafraîchir
        </Button>
      </div>

      <ImageUploader
        label="Logo de l'application"
        currentUrl={logo_url}
        endpoint="/settings/logo"
        onDone={refresh}
        testIdPrefix="logo"
      />

      <ImageUploader
        label="Image d'accueil (écran de connexion)"
        currentUrl={hero_url}
        endpoint="/settings/hero"
        onDone={refresh}
        testIdPrefix="hero"
      />

      <div className="inst-card p-5">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <SettingsIcon size={16} className="text-[#0f4c3a]" />
          Les modifications sont appliquées immédiatement après actualisation pour tous les utilisateurs.
        </div>
      </div>
    </div>
  );
}
