import { PrismaClient } from '@prisma/client';

declare global {
  // Prevent multiple PrismaClient instances during hot-reloading in dev
  // eslint-disable-next-line no-var
  var __skillgap_prisma__: PrismaClient | undefined;
}

export const prisma =
  global.__skillgap_prisma__ ||
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['warn', 'error'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') {
  global.__skillgap_prisma__ = prisma;
}

export async function disconnectPrisma(): Promise<void> {
  await prisma.$disconnect();
}
