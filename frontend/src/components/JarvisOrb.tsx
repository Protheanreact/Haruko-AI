import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, Torus } from '@react-three/drei';
import * as THREE from 'three';

const JarvisOrb = () => {
    const coreRef = useRef<THREE.Mesh>(null);
    const ring1Ref = useRef<THREE.Mesh>(null);
    const ring2Ref = useRef<THREE.Mesh>(null);
    const ring3Ref = useRef<THREE.Mesh>(null);

    useFrame((state) => {
        const time = state.clock.getElapsedTime();

        if (coreRef.current) {
            coreRef.current.rotation.y = time * 0.2;
            const scale = 1 + Math.sin(time * 2) * 0.05;
            coreRef.current.scale.set(scale, scale, scale);
        }
        if (ring1Ref.current) {
            ring1Ref.current.rotation.z = time * 0.5;
            ring1Ref.current.rotation.x = time * 0.2;
        }
        if (ring2Ref.current) {
            ring2Ref.current.rotation.z = -time * 0.3;
            ring2Ref.current.rotation.y = time * 0.4;
        }
        if (ring3Ref.current) {
            ring3Ref.current.rotation.x = -time * 0.6;
            ring3Ref.current.rotation.z = time * 0.1;
        }
    });

    return (
        <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
            {/* Pulsing Core */}
            <Sphere ref={coreRef} args={[0.8, 64, 64]}>
                <MeshDistortMaterial
                    color="#00e5ff"
                    attach="material"
                    distort={0.4}
                    speed={2}
                    roughness={0}
                    emissive="#00b8d4"
                    emissiveIntensity={2}
                    transparent
                    opacity={0.9}
                />
            </Sphere>

            {/* Outter Ring 1 */}
            <Torus ref={ring1Ref} args={[1.5, 0.02, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
                <meshStandardMaterial color="#00e5ff" emissive="#00e5ff" emissiveIntensity={5} transparent opacity={0.6} />
            </Torus>

            {/* Outter Ring 2 */}
            <Torus ref={ring2Ref} args={[1.8, 0.015, 16, 100]} rotation={[0, Math.PI / 4, 0]}>
                <meshStandardMaterial color="#00e5ff" emissive="#00e5ff" emissiveIntensity={3} transparent opacity={0.4} />
            </Torus>

            {/* Outter Ring 3 */}
            <Torus ref={ring3Ref} args={[2.1, 0.01, 16, 100]} rotation={[Math.PI / 3, Math.PI / 4, 0]}>
                <meshStandardMaterial color="#00e5ff" emissive="#00e5ff" emissiveIntensity={2} transparent opacity={0.2} />
            </Torus>

            {/* Subtle Aura */}
            <Sphere args={[1.2, 32, 32]}>
                <meshBasicMaterial color="#00e5ff" transparent opacity={0.05} side={THREE.BackSide} />
            </Sphere>
        </Float>
    );
};

export default JarvisOrb;
