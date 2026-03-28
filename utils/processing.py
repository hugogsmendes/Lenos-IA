from urllib.parse import parse_qs, urlparse


def extract_youtube_video_id(url: str) -> str | None:
	"""Extrai o ID do vídeo de uma URL do YouTube.

	Exemplos:
	- https://www.youtube.com/watch?v=atfv94Sw6LM -> atfv94Sw6LM
	- https://youtu.be/atfv94Sw6LM -> atfv94Sw6LM
	"""
	parsed_url = urlparse(url)

	if "youtu.be" in parsed_url.netloc:
		video_id = parsed_url.path.lstrip("/")
		return video_id or None

	query_params = parse_qs(parsed_url.query)
	return query_params.get("v", [None])[0]
