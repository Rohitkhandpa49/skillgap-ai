import EmbeddedPostgres from 'embedded-postgres';
import path from 'path';
import net from 'net';

function isPortOpen(port: number, host = 'localhost'): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1000);
    socket.on('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.on('error', () => {
      resolve(false);
    });
    socket.connect(port, host);
  });
}

export async function startDatabase() {
  const open = await isPortOpen(5432);
  if (open) {
    console.log('[PostgreSQL] Server already running and accepting connections on port 5432.');
    return;
  }

  const dataDir = path.resolve(process.cwd(), '.pgdata');
  console.log(`[PostgreSQL] Starting embedded database with dataDir: ${dataDir}`);

  const pg = new EmbeddedPostgres({
    databaseDir: dataDir,
    user: 'postgres',
    password: 'password',
    port: 5432,
    persistent: true,
  });

  await pg.initialise();
  await pg.start();
  try {
    await pg.createDatabase('skillgap');
  } catch {
    // Database may already exist
  }
  console.log('[PostgreSQL] Database ready on postgresql://postgres:password@localhost:5432/skillgap');
}

if (import.meta.url.endsWith(process.argv[1]) || process.argv[1]?.includes('start_db')) {
  startDatabase().catch((err) => {
    console.error('[PostgreSQL] Start failure:', err);
    process.exit(1);
  });
}
