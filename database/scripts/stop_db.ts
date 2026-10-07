import EmbeddedPostgres from 'embedded-postgres';
import path from 'path';

export async function stopDatabase() {
  const dataDir = path.resolve(process.cwd(), '.pgdata');
  const pg = new EmbeddedPostgres({
    databaseDir: dataDir,
    user: 'postgres',
    password: 'password',
    port: 5432,
    persistent: true,
  });

  try {
    await pg.stop();
    console.log('[PostgreSQL] Database stopped successfully.');
  } catch (err: any) {
    console.log('[PostgreSQL] Notice during stop:', err.message || err);
  }
}

if (import.meta.url.endsWith(process.argv[1]) || process.argv[1]?.includes('stop_db')) {
  stopDatabase().catch((err) => {
    console.error('[PostgreSQL] Stop failure:', err);
    process.exit(1);
  });
}
