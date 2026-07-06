import { z } from "zod";
import { zColor } from "@remotion/zod-types";
import {
  AbsoluteFill,
  Sequence,
  spring,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  OffthreadVideo,
} from "remotion";

// Schema para validação dos props
export const youtubeLowerThirdSchema = z.object({
  channelName: z.string().default("Remotion"),
  subscriberCount: z.string().default("46.6K"),
  avatarUrl: z.string(),
  accentColor: zColor().default("#FF0000"),
});

type YouTubeLowerThirdProps = z.infer<typeof youtubeLowerThirdSchema>;

// Durações em frames (30fps)
const SLIDE_IN_DURATION = 30;
const BUTTON_PRESS_DELAY = 90;
const BUTTON_RELEASE_DELAY = 110;
const FADE_OUT_START = 180;
const FADE_OUT_DURATION = 30;
const TOTAL_DURATION = 210;

export const YouTubeLowerThird: React.FC<YouTubeLowerThirdProps> = ({
  channelName,
  subscriberCount,
  avatarUrl,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide in animation (ease-out)
  const slideInProgress = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 200 },
  });

  const slideInY = interpolate(slideInProgress, [0, 1], [120, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const slideInOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade out animation
  const fadeOutOpacity = interpolate(
    frame,
    [FADE_OUT_START, FADE_OUT_START + FADE_OUT_DURATION],
    [1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  // Button press animation (ease-out)
  const buttonPressProgress = interpolate(
    frame,
    [BUTTON_PRESS_DELAY, BUTTON_PRESS_DELAY + 15],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  // Button release animation (spring with bounce)
  const buttonReleaseProgress = spring({
    frame: frame - BUTTON_RELEASE_DELAY,
    fps,
    config: { damping: 15, mass: 0.8, stiffness: 100 },
  });

  // Combined button scale
  const buttonScale = interpolate(
    buttonPressProgress,
    [0, 1],
    [1, 0.92],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  ) * interpolate(
    buttonReleaseProgress,
    [0, 1],
    [0.92, 1]
  );

  // Button text transition
  const showSubscribed = frame >= BUTTON_RELEASE_DELAY;

  // Overall opacity
  const overallOpacity = Math.min(slideInOpacity, fadeOutOpacity);

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 80 }}>
      <div
        style={{
          transform: `translateY(${slideInY}px)`,
          opacity: overallOpacity,
          display: "flex",
          alignItems: "center",
          gap: 16,
          backgroundColor: "white",
          borderRadius: 12,
          padding: "12px 20px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
          minWidth: 420,
        }}
      >
        {/* Avatar */}
        <img
          src={avatarUrl}
          alt={channelName}
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            objectFit: "cover",
            border: "2px solid #f0f0f0",
          }}
        />

        {/* Channel Info */}
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "#0f0f0f" }}>
            {channelName}
          </p>
          <p style={{ margin: "2px 0 0 0", fontSize: 13, color: "#606060" }}>
            {subscriberCount} subscribers
          </p>
        </div>

        {/* Subscribe Button */}
        <button
          style={{
            transform: `scale(${buttonScale})`,
            backgroundColor: showSubscribed ? "#f0f0f0" : accentColor,
            color: showSubscribed ? "#606060" : "white",
            border: "none",
            borderRadius: 20,
            padding: "8px 16px",
            fontSize: 14,
            fontWeight: 500,
            cursor: "pointer",
            transition: "background-color 0.2s ease, color 0.2s ease",
            whiteSpace: "nowrap",
          }}
        >
          {showSubscribed ? "✓ Subscribed" : "Subscribe"}
        </button>
      </div>
    </AbsoluteFill>
  );
};

export default YouTubeLowerThird;
