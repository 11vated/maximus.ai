import React, { useEffect, useRef, useState } from 'react';
import type { ThemeConfig } from '../types/theme';

interface CodeRainProps {
  theme: ThemeConfig;
  enabled?: boolean;
  density?: number;
  speed?: number;
  characters?: string;
}

const DEFAULT_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(){}[]<>?/+-=*';

export const CodeRain: React.FC<CodeRainProps> = ({
  theme,
  enabled = true,
  density = 30,
  speed = 50,
  characters = DEFAULT_CHARS
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (canvasRef.current?.parentElement) {
        setDimensions({
          width: canvasRef.current.parentElement.offsetWidth,
          height: canvasRef.current.parentElement.offsetHeight
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!enabled || !canvasRef.current || dimensions.width === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = dimensions.width;
    canvas.height = dimensions.height;

    // Determine color based on theme
    const primaryColor = theme.primary || '#00ff41';
    const textColor = primaryColor.replace(')', ', 0.8)').replace('rgb', 'rgba');
    
    // Column configuration
    const fontSize = 14;
    const columns = Math.floor(dimensions.width / fontSize);
    const drops: number[] = new Array(columns).fill(1);

    const draw = () => {
      // Semi-transparent black for trail effect
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Green text
      ctx.fillStyle = textColor;
      ctx.font = `${fontSize}px monospace`;

      for (let i = 0; i < drops.length; i++) {
        // Random character
        const char = characters[Math.floor(Math.random() * characters.length)];
        
        // Random opacity based on position (fade at top)
        const opacity = Math.random() * 0.5 + 0.5;
        ctx.globalAlpha = opacity;
        
        // Draw character
        ctx.fillText(char, i * fontSize, drops[i] * fontSize);

        // Reset drop to top randomly
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        
        drops[i]++;
      }

      ctx.globalAlpha = 1;
      animationRef.current = requestAnimationFrame(draw);
    };

    // Start animation based on speed
    const interval = setInterval(draw, speed);
    
    return () => {
      clearInterval(interval);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [enabled, dimensions, theme.primary, density, speed, characters]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-0"
      style={{
        opacity: 0.3,
        mixBlendMode: 'screen'
      }}
    />
  );
};

export default CodeRain;