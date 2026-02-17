import { Suspense } from 'react';
import { motion } from 'framer-motion';
import VRMAvatarCanvas from './VRMAvatar';

interface Theme {
  timeOfDay: 'morning' | 'day' | 'evening' | 'night';
  weather: 'clear' | 'cloudy' | 'rain' | 'snow' | 'fog';
  temperature: number;
}

interface Props {
  theme?: Theme;
  speak?: boolean; // New prop for speaking state
  phygitalMode?: string; // 'neutral', 'hot', 'cold'
  action?: string | null;
  mood?: string;
}

const WeatherOverlay = ({ weather }: { weather: string }) => {
  if (weather === 'rain') {
    return (
      <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute top-0 w-[2px] h-10 bg-blue-400/50"
            initial={{ y: -100, x: Math.random() * window.innerWidth }}
            animate={{ y: window.innerHeight + 100 }}
            transition={{ 
              duration: 0.8 + Math.random() * 0.5, 
              repeat: Infinity, 
              ease: "linear",
              delay: Math.random() * 2 
            }}
          />
        ))}
      </div>
    );
  }
  if (weather === 'snow') {
    return (
      <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute top-0 w-2 h-2 rounded-full bg-white/80 blur-[1px]"
            initial={{ y: -50, x: Math.random() * window.innerWidth }}
            animate={{ 
              y: window.innerHeight + 50,
              x: `calc(${Math.random() * 100}% + ${Math.random() * 20 - 10}px)`
            }}
            transition={{ 
              duration: 3 + Math.random() * 2, 
              repeat: Infinity, 
              ease: "linear",
              delay: Math.random() * 5 
            }}
          />
        ))}
      </div>
    );
  }
  if (weather === 'fog') {
    return (
      <div className="absolute inset-0 pointer-events-none z-20 bg-gray-400/10 backdrop-blur-[2px]" />
    );
  }
  return null;
};

const WaifuAvatar = ({ theme, speak, phygitalMode, action, mood }: Props) => {
  // Dynamic Background based on Time of Day
  const getBackgroundGradient = () => {
    switch (theme?.timeOfDay) {
      case 'morning': return 'from-purple-900 via-indigo-900 to-blue-900'; // Darker Morning (Violet/Indigo)
      case 'day': return 'from-indigo-800 via-purple-800 to-fuchsia-900'; // Day (Cyberpunk Violet/Purple)
      case 'evening': return 'from-fuchsia-900 via-purple-900 to-indigo-900'; // Evening (Deep Purple/Fuchsia)
      case 'night': return 'from-slate-900 via-purple-950 to-black'; // Night (Darkest)
      default: return 'from-gray-900 to-black';
    }
  };

  return (
    <div className={`relative w-full h-full flex items-center justify-center overflow-hidden bg-gradient-to-b ${getBackgroundGradient()}`}>
      
      {/* Background Glow Overlay - Behind Everything */}
      <div className="absolute inset-0 bg-gradient-to-t from-purple-900/50 via-transparent to-transparent pointer-events-none z-0" />

      {/* Phygital Ambient Overlay (Tablet als Fenster) */}
      <div className={`absolute inset-0 pointer-events-none z-0 transition-colors duration-1000 
           ${phygitalMode === 'hot' ? 'bg-orange-500/20 mix-blend-overlay' : ''}
           ${phygitalMode === 'cold' ? 'bg-blue-500/20 mix-blend-overlay' : ''}
       `} />

      {/* Weather Overlay - Behind Avatar (z-10) to prevent blocking view */}
      <div className="absolute inset-0 pointer-events-none z-10">
          <WeatherOverlay weather={theme?.weather ?? 'clear'} />
      </div>
      
      {/* 3D Avatar Container - On Top (z-20) */}
      <div className="relative z-20 w-full h-full">
         <Suspense fallback={<div className="absolute inset-0 flex items-center justify-center text-white z-50">Loading Haruko...</div>}>
            <VRMAvatarCanvas speak={speak} theme={theme} phygitalMode={phygitalMode} action={action} mood={mood} />
         </Suspense>
      </div>

      {/* Audio Visualizer Overlay */}
      <div className="absolute bottom-32 left-0 right-0 flex justify-center gap-1 z-20 pointer-events-none">
         {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="w-2 bg-purple-400/80 rounded-full"
              animate={{ height: [10, 10 + (20 + (i % 5) * 6), 10] }}
              transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse", delay: i * 0.05 }}
            />
         ))}
      </div>
    </div>
  );
};

export default WaifuAvatar;
