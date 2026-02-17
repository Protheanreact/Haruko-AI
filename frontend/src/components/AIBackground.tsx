import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const AIBackground = () => {
    const pointsRef = useRef<THREE.Points>(null);
    const count = 2000;

    const positions = useMemo(() => {
        const pos = new Float32Array(count * 3);
        const seeded = (index: number, offset: number) => {
            const x = Math.sin(index * 12.9898 + offset) * 43758.5453;
            return (x - Math.floor(x)) - 0.5; // deterministic 0..1 -> -0.5..0.5
        };
        for (let i = 0; i < count; i++) {
            pos[i * 3] = seeded(i, 1.23) * 20;
            pos[i * 3 + 1] = seeded(i, 7.89) * 20;
            pos[i * 3 + 2] = seeded(i, 3.21) * 20;
        }
        return pos;
    }, [count]);

    useFrame(() => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y += 0.001;
            pointsRef.current.rotation.x += 0.0005;
        }
    });

    return (
        <points ref={pointsRef}>
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={count}
                    array={positions}
                    itemSize={3}
                    args={[positions, 3]}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.05}
                color="#00e5ff"
                transparent
                opacity={0.3}
                sizeAttenuation
            />
        </points>
    );
};

export default AIBackground;
