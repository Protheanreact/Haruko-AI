import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Camera, Trash2, Plus, RefreshCw, Maximize2, AlertTriangle, Monitor } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface CameraConfig {
    id: string;
    name: string;
    url: string;
}

interface CameraDashboardProps {
    apiUrl: string;
}

export const CameraDashboard: React.FC<CameraDashboardProps> = ({ apiUrl }) => {
    const [cameras, setCameras] = useState<Record<string, CameraConfig>>({});
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showYiStream, setShowYiStream] = useState(false);
    
    // New Camera Form
    const [newId, setNewId] = useState('');
    const [newName, setNewName] = useState('');
    const [newUrl, setNewUrl] = useState('');

    const fetchCameras = async () => {
        try {
            setLoading(true);
            const resp = await axios.get(`${apiUrl}/cameras`);
            setCameras(resp.data);
        } catch (error) {
            console.error("Fehler beim Laden der Kameras", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCameras();
    }, [apiUrl]);

    const handleAddCamera = async () => {
        if (!newId || !newName || !newUrl) return;
        setAdding(true);
        try {
            await axios.post(`${apiUrl}/cameras`, { id: newId, name: newName, url: newUrl });
            setShowAddModal(false);
            setNewId('');
            setNewName('');
            setNewUrl('');
            fetchCameras();
        } catch (error) {
            console.error("Fehler beim Hinzufügen", error);
            alert("Fehler beim Hinzufügen der Kamera. Siehe Konsole.");
        } finally {
            setAdding(false);
        }
    };

    const handleRemoveCamera = async (id: string) => {
        if (!confirm(`Kamera ${id} wirklich entfernen?`)) return;
        try {
            await axios.delete(`${apiUrl}/cameras/${id}`);
            fetchCameras();
        } catch (error) {
            console.error("Fehler beim Entfernen", error);
        }
    };

    const launchYiClient = async () => {
        try {
            await axios.post(`${apiUrl}/execute`, { command: 'launch --app yi' });
            // Optional: Notification or simple alert
            // alert("Yi IoT Client wird auf dem PC gestartet...");
        } catch (error) {
            console.error("Fehler beim Starten:", error);
            alert("Fehler beim Starten des Yi Clients.");
        }
    };

    return (
        <div className="h-full w-full flex flex-col p-4 text-white">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold flex items-center gap-2 text-green-400">
                    <Camera size={28} />
                    Kamera Überwachung
                </h2>
                <div className="flex gap-2">
                    <button 
                        onClick={() => setShowYiStream(!showYiStream)}
                        className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg ${
                            showYiStream 
                            ? 'bg-red-600 hover:bg-red-500 shadow-red-900/20' 
                            : 'bg-purple-600 hover:bg-purple-500 shadow-purple-900/20'
                        }`}
                        title="Live Stream vom PC-Fenster"
                    >
                        <Monitor size={18} /> {showYiStream ? 'Yi Stream aus' : 'Yi Stream an'}
                    </button>
                    <button 
                        onClick={launchYiClient}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-blue-900/20"
                        title="Yi IoT PC Client auf dem Server starten"
                    >
                        <Maximize2 size={18} /> Start Yi App
                    </button>
                    <button 
                        onClick={() => setShowAddModal(true)}
                        className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-green-900/20"
                    >
                        <Plus size={18} /> Kamera hinzufügen
                    </button>
                </div>
            </div>

            {showYiStream ? (
                <div className="flex-1 flex flex-col items-center justify-center bg-black/50 rounded-xl p-4 border border-white/10">
                    <h3 className="text-xl mb-4 text-purple-300 animate-pulse">Live Stream vom Server (Yi IoT)</h3>
                    <div className="relative w-full h-full max-w-4xl border-2 border-purple-500/30 rounded-lg overflow-hidden shadow-2xl">
                         <img 
                            src={`${apiUrl}/stream/yi`} 
                            alt="Yi Stream" 
                            className="w-full h-full object-contain bg-black"
                         />
                         <div className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded animate-pulse">LIVE</div>
                    </div>
                    <p className="text-gray-400 text-sm mt-4">
                        Hinweis: Das "Yi IoT" Fenster muss auf dem Server geöffnet sein. Klicke auf "Start Yi App", falls du nichts siehst.
                    </p>
                </div>
            ) : loading ? (
                <div className="flex-1 flex items-center justify-center text-gray-400 animate-pulse">
                    Lade Kameras...
                </div>
            ) : Object.keys(cameras).length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-gray-700 rounded-xl m-4">
                    <Camera size={48} className="mb-4 opacity-50" />
                    <p>Keine Kameras konfiguriert.</p>
                    <p className="text-sm mt-2">Füge deine RTSP-Streams hinzu.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto pb-20">
                    {Object.entries(cameras).map(([id, cam]) => (
                        <motion.div 
                            key={id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden shadow-xl backdrop-blur-sm group"
                        >
                            {/* Header */}
                            <div className="p-3 bg-gray-900/80 flex justify-between items-center border-b border-gray-700">
                                <h3 className="font-semibold text-gray-200">{cam.name}</h3>
                                <div className="flex gap-2">
                                    <button 
                                        onClick={() => handleRemoveCamera(id)}
                                        className="p-1.5 text-red-400 hover:bg-red-900/30 rounded transition-colors"
                                        title="Entfernen"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                            
                            {/* Live View */}
                            <div className="relative aspect-video bg-black flex items-center justify-center group">
                                <img 
                                    src={`${apiUrl}/cameras/${id}/stream`} 
                                    alt={cam.name}
                                    className="w-full h-full object-contain"
                                    onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                        e.currentTarget.nextElementSibling?.classList.remove('hidden');
                                    }}
                                />
                                <div className="hidden absolute inset-0 flex flex-col items-center justify-center text-gray-500 bg-gray-900/90">
                                    <AlertTriangle size={32} className="mb-2 text-yellow-500" />
                                    <span>Stream nicht verfügbar</span>
                                    <span className="text-xs text-gray-600 mt-1">Prüfe Verbindung...</span>
                                </div>
                                
                                {/* Overlay Controls */}
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100 pointer-events-none">
                                    <div className="bg-black/60 px-3 py-1 rounded-full text-xs font-mono text-green-400 backdrop-blur-sm">
                                        LIVE
                                    </div>
                                </div>
                            </div>
                            
                            {/* Footer Info */}
                            <div className="p-2 bg-gray-900/50 text-[10px] text-gray-500 font-mono truncate px-4">
                                URL: {cam.url}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Add Modal */}
            <AnimatePresence>
                {showAddModal && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
                    >
                        <motion.div 
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            className="bg-gray-800 border border-gray-600 rounded-xl p-6 w-full max-w-md shadow-2xl"
                        >
                            <h3 className="text-xl font-bold mb-4 text-white">Neue Kamera</h3>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">ID (intern)</label>
                                    <input 
                                        value={newId} 
                                        onChange={e => setNewId(e.target.value)}
                                        placeholder="cam1"
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-green-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Name (Anzeige)</label>
                                    <input 
                                        value={newName} 
                                        onChange={e => setNewName(e.target.value)}
                                        placeholder="Wohnzimmer"
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-green-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">RTSP URL</label>
                                    <input 
                                        value={newUrl} 
                                        onChange={e => setNewUrl(e.target.value)}
                                        placeholder="rtsp://admin:123456@192.168.1.100:554/stream1"
                                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-green-500 outline-none font-mono text-xs"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 mt-6">
                                <button 
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 text-gray-300 hover:text-white"
                                >
                                    Abbrechen
                                </button>
                                <button 
                                    onClick={handleAddCamera}
                                    disabled={adding}
                                    className={`px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded shadow-lg shadow-green-900/20 flex items-center gap-2 ${adding ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    {adding ? <RefreshCw className="animate-spin" size={18} /> : <Plus size={18} />}
                                    {adding ? 'Speichere...' : 'Hinzufügen'}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
