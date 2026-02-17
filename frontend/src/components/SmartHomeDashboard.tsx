import { useEffect, useState } from 'react';
import axios from 'axios';
import { Power, Zap, Box } from 'lucide-react';

interface Device {
    name: string;
    id: string;
    type: string;
    state?: string; // Future: track state
}

const SmartHomeDashboard = () => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);
    // Force relative path for Vite Proxy to handle HTTPS->HTTP
    const API_URL = ''; 

    const fetchDevices = async () => {
        try {
            const resp = await axios.get(`${API_URL}/devices`);
            setDevices(resp.data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to fetch devices", err);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices();
    }, []);

    const sendCommand = async (device: string, state: string) => {
        try {
            await axios.post(`${API_URL}/execute`, {
                command: `tuya_control --device "${device}" --state "${state}"`
            });
            // Show toast/feedback?
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-6 h-full overflow-y-auto pb-32">
            <h2 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
                <Box className="w-8 h-8 text-purple-400" />
                Smart Home Control
            </h2>

            {loading ? (
                <div className="text-white/50">Lade Geräte...</div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {devices.map((dev) => (
                        <div key={dev.id} className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/5 shadow-lg flex flex-col justify-between h-48">
                            <div className="flex justify-between items-start">
                                <span className="text-xl font-medium text-white truncate">{dev.name}</span>
                                <Zap className="w-5 h-5 text-yellow-400" />
                            </div>
                            
                            <div className="flex gap-2 mt-4">
                                <button 
                                    onClick={() => sendCommand(dev.name, 'on')}
                                    className="flex-1 py-4 bg-green-500/20 hover:bg-green-500/40 text-green-300 rounded-xl font-bold transition-all active:scale-95 flex items-center justify-center gap-2"
                                >
                                    <Power size={20} /> AN
                                </button>
                                <button 
                                    onClick={() => sendCommand(dev.name, 'off')}
                                    className="flex-1 py-4 bg-red-500/20 hover:bg-red-500/40 text-red-300 rounded-xl font-bold transition-all active:scale-95 flex items-center justify-center gap-2"
                                >
                                    <Power size={20} /> AUS
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
            
            {devices.length === 0 && !loading && (
                <div className="text-white/30 text-center mt-20">
                    Keine Geräte gefunden.
                </div>
            )}
        </div>
    );
};

export default SmartHomeDashboard;
