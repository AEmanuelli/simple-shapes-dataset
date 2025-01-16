import shutil
import tarfile
from pathlib import Path

import click
import requests
from tqdm import tqdm

from simple_shapes_dataset.cli.migration import migrate_dataset

DATASET_URL = "https://zenodo.org/records/8112838/files/simple_shapes_dataset.tar.gz"


def downlad_file(url: str, path: Path):
    with (
        requests.get(url, stream=True) as response,
        open(path, "wb") as handle,
    ):
        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
            for data in tqdm(response.iter_content(chunk_size=block_size)):
                progress_bar.update(len(data))
                handle.write(data)
            if total_size != 0 and progress_bar.n != total_size:
                raise RuntimeError("Could not download file.")


@click.command("download", help="Download precomputed dataset")
@click.option(
    "--path",
    "-p",
    type=click.Path(path_type=Path),
    default=".",
    help="Where to download the dataset",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Whether to force download, even if the dataset is already downloaded.",
)
@click.option(
    "--no-migration",
    is_flag=True,
    default=False,
    help=(
        "Whether to skip migration of the dataset. "
        "Useful if you need the old version of the dataset."
    ),
)
def download_dataset(path: Path, force: bool, no_migration: bool):
    dataset_path = path / "simple_shapes_dataset"
    archive_path = path / "simple_shapes_dataset.tar.gz"
    if dataset_path.exists() and not force:
        click.echo(
            "Dataset already exists. Skipping download. "
            "Use `--force` to download anyway."
        )
        return
    elif dataset_path.exists():
        click.echo("Dataset already exists. Re-downloading.")
        shutil.rmtree(dataset_path)
    downlad_file(DATASET_URL, archive_path)
    click.echo("Extracting archive...")
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(path)
    archive_path.unlink()

    if not no_migration:
        migrate_dataset(path, False)
