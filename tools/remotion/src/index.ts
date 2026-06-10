import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";
import { loadFont as loadCinzel } from "@remotion/google-fonts/Cinzel";
import { loadFont as loadEBGaramond } from "@remotion/google-fonts/EBGaramond";
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";

// Carregar fontes premium para a fábrica
// loadCinzel(); // temporariamente desativado para debug
// loadEBGaramond();
// loadMontserrat();

registerRoot(RemotionRoot);
