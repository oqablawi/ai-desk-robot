import argparse

from .app import RobotDisplayApp
from .config import RobotConfig
from .spotify import BackgroundPlaybackProvider, DemoSpotifyProvider, SpotifyWebApiProvider, authorize_spotify
from .voice import VoiceLoop


def main() -> None:
    config = RobotConfig.from_environment()
    parser = argparse.ArgumentParser(description="AI desk robot display")
    parser.add_argument("--scale", type=int, choices=(1, 2, 3), default=config.scale,
                        help="Desktop zoom; the logical screen is always 480 x 320")
    parser.add_argument(
        "--screen",
        choices=("idle", "listening", "thinking", "speaking", "happy", "sleeping", "error", "music",
                 "eyes", "spotify"),
        default=config.start_screen,
        help="Starting screen. eyes and spotify are older names for idle and music.",
    )
    parser.add_argument("--fullscreen", action=argparse.BooleanOptionalAction, default=config.fullscreen)
    parser.add_argument("--mode", choices=("demo", "spotify"), default=config.mode)
    parser.add_argument("--demo", action="store_true",
                        help="run the scripted mode-switch demo on launch")
    parser.add_argument("--spotify-login", action="store_true", help="perform one-time Spotify PKCE login")
    args = parser.parse_args()
    if args.spotify_login:
        if not config.spotify_client_id:
            parser.error("Set SPOTIFY_CLIENT_ID in .env first")
        authorize_spotify(config.spotify_client_id, config.spotify_redirect_uri, config.spotify_token_file)
        return
    provider = (BackgroundPlaybackProvider(SpotifyWebApiProvider(token_file=config.spotify_token_file))
                if args.mode == "spotify" else DemoSpotifyProvider())
    app = RobotDisplayApp(provider=provider, scale=args.scale, fullscreen=args.fullscreen)
    app.set_mode(args.screen)
    voice = VoiceLoop(
        app.robot,
        api_key=config.xai_api_key,
        model=config.xai_model,
        base_url=config.xai_base_url,
        tts_voice=config.xai_tts_voice,
        playback_fn=provider.current,
        provider=provider,
    )
    voice.attach_gpio(config.ptt_pin)
    app.attach_voice(voice)
    if args.demo:
        app.robot.start_demo()
    app.run()


if __name__ == "__main__":
    main()
