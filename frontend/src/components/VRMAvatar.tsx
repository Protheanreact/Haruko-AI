import { useEffect, useState, useRef, Suspense } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils, VRM } from '@pixiv/three-vrm';
import { VRMAnimation, VRMAnimationLoaderPlugin, createVRMAnimationClip, VRMLookAtQuaternionProxy } from '@pixiv/three-vrm-animation';
import { OrbitControls, Stars, useGLTF, Html, TransformControls } from '@react-three/drei';

interface VRMAvatarProps {
    modelUrl: string;
    emotion?: string;
    speak?: boolean; // Controls lip sync
    timeOfDay?: string; // For Sleep Mode
    action?: string | null; // Transient Action: bow, shock, gesticulate, wave, nod, shake
    mood?: string; // Persistent State: neutral, happy, sad, angry, surprised, tired
    phygitalMode?: string;
}

const MOOD_PRESETS: Record<string, any> = {
    neutral: { 
        expression: 'neutral', 
        pose: { headX: 0, headZ: 0, spineX: 0, spineY: 0 } 
    },
    happy: { 
        expression: 'happy', 
        pose: { headX: -0.1, headZ: -0.05, spineX: -0.05, spineY: 0 } // Head slightly up
    },
    sad: { 
        expression: 'sad', 
        pose: { headX: 0.2, headZ: 0.05, spineX: 0.1, spineY: 0 } // Head down
    },
    angry: { 
        expression: 'angry', 
        pose: { headX: 0.05, headZ: 0, spineX: 0, spineY: 0 } 
    },
    surprised: { 
        expression: 'surprised', 
        pose: { headX: -0.15, headZ: 0, spineX: -0.1, spineY: 0 } 
    },
    tired: {
        expression: 'neutral', 
        pose: { headX: 0.15, headZ: 0.05, spineX: 0.1, spineY: 0 }
    }
};

// --- Room Component ---
const Room = () => {
    const { scene } = useGLTF('/models/bed_room.glb');
    return <primitive object={scene} scale={1.0} position={[0, -1, -1]} />;
};

const Avatar = ({ modelUrl, speak, timeOfDay, action, mood = 'neutral' }: VRMAvatarProps) => {
    const [vrm, setVrm] = useState<VRM | null>(null);
    const [currentVrmAnimation, setCurrentVrmAnimation] = useState<VRMAnimation | null>(null);
    const mixerRef = useRef<THREE.AnimationMixer | null>(null);
    const { camera } = useThree();
    
    // Auto-State for Boredom/Sleep
    const [autoState, setAutoState] = useState<'idle' | 'sitting' | 'sleeping'>('idle');
    const BOREDOM_THRESHOLD = 60000; // 60 seconds to sit
    
    // Interaction States
    const [lookTarget, setLookTarget] = useState<THREE.Vector3>(new THREE.Vector3(0, 1.3, 5)); // Default: Towards camera
    const [isIdle, setIsIdle] = useState(true);
    const [lastPokeTime, setLastPokeTime] = useState(0);

    // Animation States - Cleaned up (Old procedural states removed)

    const blinkTimer = useRef(0);
    const nextBlinkTime = useRef(Math.random() * 3 + 2); // 2-5s initial
    const lastActionTime = useRef(Date.now()); // For Boredom Tracking

    // Setup Mode State
    const [setupMode, setSetupMode] = useState(false);
    const [transformMode, setTransformMode] = useState<'translate' | 'rotate'>('translate');
    const [forceSleep, setForceSleep] = useState(false);
    
    // Updated Chair Position from User
    const [chairPos, setChairPos] = useState<THREE.Vector3>(new THREE.Vector3(-1.50, -1.25, -1.69));
    const [chairRot, setChairRot] = useState<THREE.Euler>(new THREE.Euler(0, 0, 0)); 

    // Updated Bed Position from User
    const [bedPos, setBedPos] = useState<THREE.Vector3>(new THREE.Vector3(-0.72, -0.18, -0.49));
    const [bedRot, setBedRot] = useState<THREE.Euler>(new THREE.Euler(-Math.PI / 2, 4 * (Math.PI / 180), Math.PI / 2));

    // Check for Boredom / Sleep State
    useEffect(() => {
        const interval = setInterval(() => {
            if (setupMode) return; // Disable auto-states during setup

            const now = Date.now();
            const timeSinceLastAction = now - lastActionTime.current;

            // Priority 1: Sleep (Night)
            if (timeOfDay === 'night') {
                if (autoState !== 'sleeping') setAutoState('sleeping');
            }
            // Priority 2: Always Sit (Default State)
            else {
                if (autoState !== 'sitting') setAutoState('sitting');
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [timeOfDay, autoState, setupMode]);

    // Reset Boredom on Action/Speak - REMOVED to keep her sitting
    
    // Load VRM Animation (.vrma) if action matches a file or known animation
    useEffect(() => {
        if (!vrm) {
            setCurrentVrmAnimation(null);
            mixerRef.current = null;
            return;
        }

        // Initialize Mixer if not exists
        if (!mixerRef.current) {
            mixerRef.current = new THREE.AnimationMixer(vrm.scene);
        }

        // Ensure VRMLookAtQuaternionProxy exists BEFORE creating clips
        if (vrm.lookAt) {
            // @ts-ignore
            if (!vrm.lookAt.quaternionProxy) {
                 // @ts-ignore
                 vrm.lookAt.quaternionProxy = new VRMLookAtQuaternionProxy(vrm.lookAt);
            }
        }

        // Procedural Actions that should NOT stop the base animation (Sitting/Sleeping)
        const proceduralActions = ['bow', 'shock', 'gesticulate', 'wave', 'nod', 'shake', 'think', 'knock'];
        
        // Determine Effective Action
        // If action is procedural, we ignore it here so the base animation (Sitting) keeps playing
        let effectiveAction = action;
        if (proceduralActions.includes(action || '')) {
            effectiveAction = null;
        }

        let animUrl = null;

        // Map Actions/States to Files
        const animationMap: Record<string, string> = {
            'Walking': '/animations/Walking.vrma',
            'Dancing': '/animations/Dancing.vrma',
            // Explicit Sitting
            'Sitting': '/animations/Sitting.vrma',
        };

        // If no explicit action, check auto state
        if (!effectiveAction) {
            if (forceSleep) {
                 animUrl = '/animations/Sleep.vrma';
            } else if (autoState === 'sitting') {
                animUrl = '/animations/Sitting.vrma';
            } else if (autoState === 'sleeping') {
                animUrl = '/animations/Sleep.vrma';
            } else if (autoState === 'idle') {
                // Default to Sitting as requested by user
                animUrl = '/animations/Sitting.vrma';
            }
        } else {
            animUrl = animationMap[effectiveAction];
        }

        if (!effectiveAction && !animUrl) {
            setCurrentVrmAnimation(null);
            mixerRef.current.stopAllAction();
            return;
        }

        if (animUrl) {
            console.log(`Loading VRM Animation: ${animUrl} (State: ${effectiveAction || autoState})`);
            const loader = new GLTFLoader();
            loader.register((parser) => new VRMAnimationLoaderPlugin(parser));
            
            loader.load(
                animUrl,
                (gltf) => {
                    const vrmAnimations = gltf.userData.vrmAnimations;
                    if (vrmAnimations && vrmAnimations.length > 0) {
                        const anim = vrmAnimations[0];
                        setCurrentVrmAnimation(anim);
                        
                        if (mixerRef.current && vrm) {
                            mixerRef.current.stopAllAction();
                            const clip = createVRMAnimationClip(anim, vrm);
                            const action = mixerRef.current.clipAction(clip);
                            action.play();
                            console.log("VRM Animation playing");
                        }

                    } else {
                        console.warn("No VRM Animation found in file");
                        setCurrentVrmAnimation(null);
                        mixerRef.current?.stopAllAction();
                    }
                },
                undefined,
                (_error) => {
                    // console.error("Error loading VRM Animation:", error); // Suppress error for missing files
                    setCurrentVrmAnimation(null);
                    mixerRef.current?.stopAllAction();
                }
            );
        } else {
            setCurrentVrmAnimation(null);
            mixerRef.current.stopAllAction();
        }

    }, [action, vrm, autoState]);

    // Handle Transient Actions (Logging Only now)
    useEffect(() => {
        if (!vrm || !action) return;
        console.log("VRM Action Triggered:", action);
        lastActionTime.current = Date.now(); // Reset boredom
    }, [action, vrm]);

    // Random Autonomous Micro-Actions removed per user request
    // (Old procedural animation system removed)

    // Poke Handler
    const handlePoke = (event: any) => {
        if (!vrm) return;
        event.stopPropagation();
        setLastPokeTime(Date.now());
        
        const hitPoint = event.point; 
        setLookTarget(hitPoint);
        setIsIdle(false);
        setTimeout(() => {
             setLookTarget(new THREE.Vector3(0, 1.3, 5));
             setIsIdle(true);
        }, 2000);

        const y = hitPoint.y;
        let reactionText = "";
        let emotion = "neutral";
        
        if (y > 1.45) {
            console.log("Poke: HEAD");
            reactionText = "Hey, nicht die Frisur!";
            emotion = "angry";
        } else if (y > 1.0) {
            console.log("Poke: BODY");
            reactionText = "Bin ich dick?";
            emotion = "surprised";
        } else {
             reactionText = "Huch!";
             emotion = "fun";
        }

        fetch('/tts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: reactionText })
        })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.play();
        })
        .catch(err => console.error("TTS Error:", err));

        if (vrm.expressionManager) {
            vrm.expressionManager.setValue(emotion, 1.0);
            setTimeout(() => {
                vrm.expressionManager?.setValue(emotion, 0);
            }, 1500);
        }
    };

    // Load VRM
    useEffect(() => {
        const loader = new GLTFLoader();
        loader.register((parser) => new VRMLoaderPlugin(parser));

        console.log("Loading VRM from:", modelUrl);
        loader.load(
            modelUrl,
            (gltf) => {
                const vrm = gltf.userData.vrm;
                if (!vrm) return;
                VRMUtils.removeUnnecessaryVertices(gltf.scene);
                VRMUtils.combineSkeletons(gltf.scene);
                vrm.scene.rotation.y = Math.PI;
                
                // Init A-Pose
                const leftUpperArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
                const rightUpperArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
                if (leftUpperArm) leftUpperArm.rotation.z = Math.PI / 2.5; 
                if (rightUpperArm) rightUpperArm.rotation.z = -Math.PI / 2.5;

                // Fix for VRMLookAtQuaternionProxy warning
                if (vrm.lookAt) {
                    // @ts-ignore
                    if (!vrm.lookAt.quaternionProxy) {
                         // @ts-ignore
                         vrm.lookAt.quaternionProxy = new VRMLookAtQuaternionProxy(vrm.lookAt);
                    }
                }

                setVrm((prev) => {
                    if (prev) VRMUtils.deepDispose(prev.scene);
                    return vrm;
                });
            },
            undefined,
            (error) => console.error('Error loading VRM:', error)
        );

        return () => {
            setVrm(prev => {
                if (prev) VRMUtils.deepDispose(prev.scene);
                return null;
            });
        };
    }, [modelUrl]);

    // Animation Loop
    useFrame((state, delta) => {
        if (!vrm) return;
        
        // Update Mixer (for .vrma)
        if (mixerRef.current) {
            mixerRef.current.update(delta);
        }

        vrm.update(delta);

        const t = state.clock.elapsedTime;
        const isSleeping = timeOfDay === 'night' && isIdle;

        // --- Mood Blending (Expressions Only) ---
        const targetMood = MOOD_PRESETS[mood] || MOOD_PRESETS['neutral'];
        
        // Apply Facial Expression (Mood)
        if (vrm.expressionManager) {
            ['neutral', 'happy', 'sad', 'angry', 'surprised'].forEach(exp => {
                const val = vrm.expressionManager?.getValue(exp) || 0;
                // Fade out if not current mood
                if (exp !== targetMood.expression) {
                     vrm.expressionManager?.setValue(exp, THREE.MathUtils.lerp(val, 0, delta * 5));
                }
            });
            // Fade in current mood
            const currentVal = vrm.expressionManager.getValue(targetMood.expression) || 0;
            // If sleeping, override with neutral
            const targetVal = isSleeping ? 0 : 0.5; // Base intensity
            vrm.expressionManager.setValue(targetMood.expression, THREE.MathUtils.lerp(currentVal, targetVal, delta * 5));
        }

        // --- Blinking ---
        if (isSleeping) {
             vrm.expressionManager?.setValue('blink', 1.0);
        } else {
             // Random blinking
             blinkTimer.current += delta;
             if (blinkTimer.current > nextBlinkTime.current) {
                 vrm.expressionManager?.setValue('blink', 1.0);
                 if (blinkTimer.current > nextBlinkTime.current + 0.1) {
                     blinkTimer.current = 0;
                     nextBlinkTime.current = Math.random() * 3 + 2;
                     vrm.expressionManager?.setValue('blink', 0);
                 }
             } else {
                 vrm.expressionManager?.setValue('blink', 0);
             }
        }

        // --- Lip Sync ---
        if (speak && !isSleeping) {
             const volume = Math.sin(t * 20) * 0.5 + 0.5; // Mock audio level
             vrm.expressionManager?.setValue('aa', volume);
        } else {
             vrm.expressionManager?.setValue('aa', 0);
        }
        
        // --- LookAt Camera (Only if not sleeping) ---
        if (!isSleeping && !setupMode && vrm.lookAt) {
             vrm.lookAt.target = camera;
        }

    });


    // --- Position Logic for Sitting/Sleeping ---
    // These offsets depend on the room model (bed_room.glb)
    const getGroupPosition = () => {
        // Always use Chair Position for Sitting OR Idle (since Idle is now Sitting)
        if (action === 'Sitting' || autoState === 'sitting' || autoState === 'idle') {
            return { pos: chairPos, rot: chairRot }; 
        }
        if (autoState === 'sleeping' || forceSleep) {
            return { pos: bedPos, rot: bedRot };
        }
        // Fallback (should rarely be reached now)
        return { pos: new THREE.Vector3(0, -1, 0), rot: new THREE.Euler(0, Math.PI, 0) };
    };

    const { pos, rot } = getGroupPosition();

    // Toggle Setup Mode via Key (e.g., 'S')
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.shiftKey) {
                if (e.key === 'S') {
                    setSetupMode(prev => !prev);
                    console.log("Setup Mode Toggled");
                }
                if (e.key === 'L') {
                    setForceSleep(prev => !prev);
                    console.log("Force Sleep Toggled");
                }
                if (e.key === 'R') {
                    setTransformMode(prev => prev === 'translate' ? 'rotate' : 'translate');
                    console.log("Transform Mode Toggled");
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    if (vrm) {
        return (
            <>
                <group onClick={handlePoke} position={pos} rotation={rot instanceof THREE.Euler ? rot : new THREE.Euler(...rot as [number, number, number])}>
                    <primitive object={vrm.scene} />
                </group>

                {setupMode && (
                    <>
                        {/* Chair Marker */}
                        <TransformControls 
                            position={chairPos} 
                            rotation={chairRot}
                            mode={transformMode}
                            onObjectChange={(e: any) => {
                                if (e?.target?.object) {
                                    if (transformMode === 'translate') {
                                        setChairPos(e.target.object.position.clone());
                                    } else {
                                        setChairRot(e.target.object.rotation.clone());
                                    }
                                    const obj = e.target.object;
                                    console.log(`Chair Pos: ${obj.position.x.toFixed(2)}, ${obj.position.y.toFixed(2)}, ${obj.position.z.toFixed(2)} | Rot: ${(obj.rotation.x * 180/Math.PI).toFixed(0)}°, ${(obj.rotation.y * 180/Math.PI).toFixed(0)}°, ${(obj.rotation.z * 180/Math.PI).toFixed(0)}°`);
                                }
                            }}
                        >
                            <mesh>
                                <boxGeometry args={[0.3, 0.3, 0.3]} />
                                <meshStandardMaterial color="orange" wireframe />
                            </mesh>
                        </TransformControls>

                        {/* Bed Marker */}
                        <TransformControls 
                            position={bedPos} 
                            rotation={bedRot}
                            mode={transformMode}
                            onObjectChange={(e: any) => {
                                if (e?.target?.object) {
                                    if (transformMode === 'translate') {
                                        setBedPos(e.target.object.position.clone());
                                    } else {
                                        setBedRot(e.target.object.rotation.clone());
                                    }
                                    const obj = e.target.object;
                                    console.log(`Bed Pos: ${obj.position.x.toFixed(2)}, ${obj.position.y.toFixed(2)}, ${obj.position.z.toFixed(2)} | Rot: ${(obj.rotation.x * 180/Math.PI).toFixed(0)}°, ${(obj.rotation.y * 180/Math.PI).toFixed(0)}°, ${(obj.rotation.z * 180/Math.PI).toFixed(0)}°`);
                                }
                            }}
                        >
                            <mesh>
                                <boxGeometry args={[0.5, 0.2, 0.8]} />
                                <meshStandardMaterial color="cyan" wireframe />
                            </mesh>
                        </TransformControls>
                        
                        <Html position={[0, 2, 0]} center>
                            <div style={{ background: 'rgba(0,0,0,0.7)', color: 'white', padding: '10px', borderRadius: '5px', pointerEvents: 'none' }}>
                                <h3>Setup Mode</h3>
                                <p>Shift+S: Toggle Mode | Shift+L: Force Sleep | Shift+R: Translate/Rotate</p>
                                <p>Chair: {chairPos.x.toFixed(2)}, {chairPos.y.toFixed(2)}, {chairPos.z.toFixed(2)} (Rot: {(chairRot.x * 180/Math.PI).toFixed(0)}°, {(chairRot.y * 180/Math.PI).toFixed(0)}°, {(chairRot.z * 180/Math.PI).toFixed(0)}°)</p>
                                <p>Bed: {bedPos.x.toFixed(2)}, {bedPos.y.toFixed(2)}, {bedPos.z.toFixed(2)} (Rot: {(bedRot.x * 180/Math.PI).toFixed(0)}°, {(bedRot.y * 180/Math.PI).toFixed(0)}°, {(bedRot.z * 180/Math.PI).toFixed(0)}°)</p>
                            </div>
                        </Html>
                    </>
                )}
            </>
        );
    }
    return null;
};

// --- Dynamic Environment Component ---
const DynamicEnvironment = ({ theme }: { theme?: { timeOfDay: string, weather: string } }) => {
    const timeOfDay = theme?.timeOfDay || 'day';
    let sunPosition: [number, number, number] = [0, 10, 0];
    switch (timeOfDay) {
        case 'morning': sunPosition = [100, 10, 100]; break;
        case 'day': sunPosition = [0, 100, 0]; break;
        case 'evening': sunPosition = [-100, 10, 100]; break;
        case 'night': sunPosition = [0, -10, 0]; break;
    }
    const isNight = timeOfDay === 'night';

    return (
        <>
            {isNight && (
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
            )}
            <ambientLight intensity={isNight ? 0.3 : 1.0} />
            <directionalLight 
                position={sunPosition} 
                intensity={isNight ? 0.2 : 1.5} 
                color={isNight ? "#4444ff" : "white"} 
            />
        </>
    );
};

const VRMAvatarCanvas = ({ speak, modelUrl, theme, action, mood }: { 
    speak?: boolean, 
    modelUrl?: string, 
    theme?: { timeOfDay: string, weather: string },
    action?: string | null,
    mood?: string,
    phygitalMode?: string
}) => {
    // Default to avatar.vrm if no modelUrl is provided
    const activeModel = modelUrl || '/models/avatar.vrm';
    const timeOfDay = theme?.timeOfDay || 'day';

    return (
        <div className="w-full h-full relative">
            <Canvas 
                camera={{ position: [0, 1.4, 1.5], fov: 40 }} 
                shadows 
                gl={{ preserveDrawingBuffer: true, alpha: true }}
            >
                {/* Dynamische Umgebung */}
                <DynamicEnvironment theme={theme} />
                
                {/* Room hinzufügen */}
                <Suspense fallback={null}>
                    <Room />
                </Suspense>

                {/* Avatar hinzufügen */}
                <Suspense fallback={<Html center><div>Lade Avatar...</div></Html>}>
                    <Avatar modelUrl={activeModel} speak={speak} timeOfDay={timeOfDay} action={action} mood={mood} />
                </Suspense>

                <OrbitControls 
                    makeDefault
                    target={[0, 1.3, 0]} 
                    enablePan={true}
                    enableZoom={true}
                    enableRotate={true}
                    minDistance={0.5}
                    maxDistance={5}
                />
            </Canvas>
        </div>
    );
};

export default VRMAvatarCanvas;