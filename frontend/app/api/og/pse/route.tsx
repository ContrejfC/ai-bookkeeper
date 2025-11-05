import { ImageResponse } from 'next/og';

export const runtime = 'edge';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const slug = searchParams.get('slug') || '';
  const title = slug.replace(/-export-csv$/,'').replace(/-/g,' ') + ' — Export CSV';

  const res = new ImageResponse(
    (
      <div style={{ display:'flex', width:'100%', height:'100%', background:'#0b1220', color:'#fff', padding:'64px', fontSize:64 }}>
        <div>{title}</div>
      </div>
    ),
    { width: 1200, height: 630 }
  );

  (res as any).headers.set('Cache-Control','public, max-age=86400, stale-while-revalidate=604800');
  return res;
}
