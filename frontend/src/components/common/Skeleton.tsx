import React from 'react';
import './Skeleton.css';

export interface SkeletonProps {
    variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
    width?: string | number;
    height?: string | number;
    sx?: React.CSSProperties;
    animation?: 'pulse' | 'wave' | false;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    variant = 'text',
    width,
    height,
    sx = {},
    animation = 'pulse',
}) => {
    const classes = [
        'skeleton',
        `skeleton-${variant}`,
        animation ? `skeleton-${animation}` : '',
    ].filter(Boolean).join(' ');

    const style: React.CSSProperties = {
        ...(width && { width }),
        ...(height && { height }),
        ...sx,
    };

    return <span className={classes} style={style} aria-hidden="true" />;
};

export interface SkeletonTextProps {
    lines?: number;
    width?: string | number;
    maxWidth?: string | number;
    height?: string | number;
    spacing?: number;
}

export const SkeletonText: React.FC<SkeletonTextProps> = ({
    lines = 1,
    width = '100%',
    maxWidth,
    height = '1em',
    spacing = 8,
}) => {
    return (
        <div className="skeleton-text-container" style={{ maxWidth: maxWidth as string }}>
            {Array.from({ length: lines }).map((_, index) => (
                <Skeleton
                    key={index}
                    variant="text"
                    width={index === lines - 1 && lines > 1 ? '60%' : width}
                    height={height}
                    sx={{
                        marginBottom: index < lines - 1 ? spacing : 0,
                    }}
                />
            ))}
        </div>
    );
};

export interface SkeletonCardProps {
    showImage?: boolean;
    showTitle?: boolean;
    showText?: boolean;
    textLines?: number;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
    showImage = true,
    showTitle = true,
    showText = true,
    textLines = 3,
}) => {
    return (
        <div className="skeleton-card">
            {showImage && (
                <Skeleton
                    variant="rectangular"
                    width="100%"
                    height={120}
                    sx={{ borderRadius: '8px 8px 0 0' }}
                />
            )}
            <div className="skeleton-card-content" style={{ padding: '16px' }}>
                {showTitle && (
                    <Skeleton
                        variant="text"
                        width="70%"
                        height="1.5em"
                        sx={{ marginBottom: 2 }}
                    />
                )}
                {showText && (
                    <SkeletonText lines={textLines} />
                )}
            </div>
        </div>
    );
};

export default Skeleton;
