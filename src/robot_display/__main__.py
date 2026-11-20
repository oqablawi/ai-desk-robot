import argparse

from .app import RobotDisplayApp
from .config import RobotConfig
from .spotify import BackgroundPlaybackProvider, DemoSpotifyProvider, SpotifyWebApiProvider, authorize_spotify


def main() -> None:
    config = RobotConfig.from_environment()
    parser = argparse.ArgumentParser(description="AI desk robot display")
    parser.add_argument("--scale", type=int, choices=(1, 2, 3), default=config.scale,
                        help="Desktop zoom; the logical screen is always 480 x 320")
    parser.add_argument("--screen", choices=("eyes", "spotify", "talk"), default=config.start_screen)
    parser.add_argument("--fullscreen", action=argparse.BooleanOptionalAction, default=config.fullscreen)
    parser.add_argument("--mode", choices=("demo", "spotify"), default=config.mode)
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
    app.run()


if __name__ == "__main__":
    main()
