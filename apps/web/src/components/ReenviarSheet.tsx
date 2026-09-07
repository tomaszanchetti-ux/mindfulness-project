// WS29 · C0 · El panel "Reenviar": elegir a alguien de mi comunidad (reenvío
// dentro de la app) o mandar el link por WhatsApp. Lo usan la ficha ajena
// (C2.1) y la ficha propia del Baúl (C2.2). C2.1 lo implementa; hasta entonces,
// esta es la INTERFAZ (no la cambies sin avisar al orquestador):
//
//   <ReenviarSheet entregaId={id} abierto={bool} onClose={() => …}
//                  linkWhatsApp="https://…" />
//
// - `entregaId`: la Pausa que se reenvía (propia o ajena; el backend decide).
// - `linkWhatsApp`: el link que viaja por WhatsApp. Ficha propia: el link de
//   regalo `/c/{token}` (se crea con `api.compartir`); ficha ajena: el link
//   in-app `${origin}/comunidad/ficha/${entregaId}` (con login y la regla de lectura).

export interface ReenviarSheetProps {
  entregaId: string;
  abierto: boolean;
  onClose: () => void;
  linkWhatsApp: string | null;
}

export function ReenviarSheet(_props: ReenviarSheetProps) {
  return null;
}
