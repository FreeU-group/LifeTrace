const https = require('https');
const fs = require('fs');
const path = require('path');

// 创建lib目录
const libDir = path.join(__dirname, 'lib');
if (!fs.existsSync(libDir)) {
    fs.mkdirSync(libDir);
}

// 下载文件的函数
function downloadFile(url, filename) {
    return new Promise((resolve, reject) => {
        const filePath = path.join(libDir, filename);
        const file = fs.createWriteStream(filePath);

        https.get(url, (response) => {
            response.pipe(file);

            file.on('finish', () => {
                file.close();
                console.log(`✓ Downloaded ${filename}`);
                resolve();
            });

            file.on('error', (err) => {
                fs.unlink(filePath, () => {}); // 删除部分下载的文件
                reject(err);
            });
        }).on('error', (err) => {
            reject(err);
        });
    });
}

// 要下载的文件列表
const downloads = [
    {
        url: 'https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js',
        filename: 'marked.min.js'
    },
    {
        url: 'https://unpkg.com/lucide@latest/dist/umd/lucide.js',
        filename: 'lucide.js'
    }
];

// 执行下载
async function downloadDependencies() {
    console.log('Downloading dependencies...');

    try {
        for (const download of downloads) {
            await downloadFile(download.url, download.filename);
        }
        console.log('✓ All dependencies downloaded successfully!');
    } catch (error) {
        console.error('✗ Error downloading dependencies:', error.message);
        process.exit(1);
    }
}

downloadDependencies();
