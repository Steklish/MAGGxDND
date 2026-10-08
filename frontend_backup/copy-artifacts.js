import { copyFileSync, mkdirSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const srcArts = join(__dirname, 'arts');
const distArts = join(__dirname, 'dist', 'arts');

function copyDirRecursive(src, dest) {
    if (!statSync(src).isDirectory()) {
        return;
    }
    
    if (!statSync(dest, { throwIfNoEntry: false })) {
        mkdirSync(dest, { recursive: true });
    }
    
    const entries = readdirSync(src, { withFileTypes: true });
    
    for (const entry of entries) {
        const srcPath = join(src, entry.name);
        const destPath = join(dest, entry.name);
        
        if (entry.isDirectory()) {
            copyDirRecursive(srcPath, destPath);
        } else {
            copyFileSync(srcPath, destPath);
        }
    }
}

try {
    copyDirRecursive(srcArts, distArts);
    console.log('✓ Copied arts folder to dist');
} catch (error) {
    console.error('⚠ Could not copy arts folder:', error.message);
    process.exit(1);
}
