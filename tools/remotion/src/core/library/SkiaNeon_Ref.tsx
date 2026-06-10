// @ts-nocheck
import {
    Blur,
    Fill,
    fitbox,
    Group,
    LinearGradient,
    mix,
    Path,
    processTransform2d,
    rect,
    Skia,
    topLeft,
    topRight,
} from "@shopify/react-native-skia";
import React, { useMemo } from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Este arquivo é uma REFERÊNCIA para uso do Skia no Remotion para efeitos Neon e Shaders.
// Requer a instalação de @shopify/react-native-skia e canvaskit-wasm.

const CLAMP = {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
} as const;
const PADDING = 200;
const src = rect(0, 0, 2630, 1325);

const duration = 15;

export const durationInFrames = 500;

export const SkiaNeon: React.FC<{
    readonly color1: string;
    readonly color2: string;
}> = ({ color1, color2 }) => {
    const config = useVideoConfig();
    const frame = useCurrentFrame();

    const defaultPath = useMemo(() => {
        return [
            {
                path: "M337 1240.85C255.37 1240.85 172.05 1218.91 95.1298 1176.32C66.9098 1160.69 56.6998 1125.15 72.3198 1096.92C87.9498 1068.7 123.49 1058.49 151.72 1074.11C234.05 1119.7 324.75 1134.72 407.1 1116.45C477.65 1100.79 536.83 1061.09 565.4 1010.25C617.62 917.33 559.54 810.94 410.02 725.65C336.2 683.54 280.74 631.74 245.18 571.68C212.25 516.07 197.94 455.14 203.79 395.47C213.51 296.33 278.64 212.57 369.71 182.08C421.12 164.87 556.28 141.83 700.95 299.09C722.79 322.83 721.25 359.78 697.51 381.62C673.77 403.46 636.82 401.92 614.98 378.18C545.69 302.86 469.82 271.77 406.8 292.85C359.34 308.74 325.29 353.49 320.06 406.85C316.65 441.64 325.52 478.05 345.71 512.15C370.81 554.54 411.93 592.23 467.91 624.16C574.82 685.15 646.14 757.33 679.89 838.69C711.63 915.24 707.15 996.48 667.25 1067.47C622 1147.98 536.41 1207.39 432.43 1230.48C401.23 1237.4 369.25 1240.83 337.02 1240.83L337 1240.85Z",
                colors: [color1, color2],
                index: 0,
            },
            // ... outras paths omitidas para brevidade na referência
        ];
    }, [color1, color2]);

    const dst = rect(
        PADDING,
        PADDING,
        config.width - PADDING * 2,
        config.height - PADDING * 2,
    );
    const progresses = [
        interpolate(frame, [0, duration], [0, 1], CLAMP),
        // ...
    ];

    const paths = defaultPath.map((def) => {
        const path = Skia.Path.MakeFromSVGString(def.path)!;
        path.transform(processTransform2d(fitbox("contain", src, dst)));
        const bounds = path.computeTightBounds();
        const { colors } = def;
        return {
            path,
            bounds,
            colors,
            progress: progresses[def.index]!,
        };
    });

    const b1 = 8;
    const progress8 = progresses[progresses.length - 1]!;
    const blur1 = mix(progress8, b1 * 2, b1);

    return (
        <>
            <Fill color="black" />
            {paths.map(({ path, colors, bounds, progress }, i) => (
                <React.Fragment key={i}>
                    <Group clip={path}>
                        <Fill color={`rgba(0,0,0, ${progress})`} />
                    </Group>
                    <Path
                        path={path}
                        strokeCap="round"
                        strokeJoin="round"
                        end={progress}
                        style="stroke"
                        strokeWidth={15}
                    >
                        <LinearGradient
                            colors={colors}
                            start={topLeft(bounds)}
                            end={topRight(bounds)}
                        />
                        <Blur
                            blur={interpolate(progress, [0, 0.5, 1], [0, blur1 * 2, blur1])}
                        />
                    </Path>
                </React.Fragment>
            ))}
        </>
    );
};
