import shutil
import tarfile
from pathlib import Path
import click
import requests
from tqdm import tqdm
from simple_shapes_dataset.cli.migration import migrate_dataset

DATASET_URL = "https://zenodo.org/records/8112838/files/simple_shapes_dataset.tar.gz"
# LIGHT_DATASET_URL = "https://drive.usercontent.google.com/download?id=1gZt7xg2ZqUwo1kKZPghVz3DxY8Rm0epT&export=download&authuser=1&confirm=t&uuid=b748272e-5362-44bb-a8e8-0991426eb185&at=AEz70l4BoHSbKwhVGJgu8hGIiVxv:1740761553787"

def downlad_file(url: str, path: Path):
    with requests.get(url, stream=True) as response, open(path, "wb") as handle:
        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
            for data in response.iter_content(chunk_size=block_size):
                progress_bar.update(len(data))
                handle.write(data)

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
@click.option(
    "--light",
    is_flag=True,
    default=False,
    help="Download the light version of the dataset",
)
def download_dataset(path: Path, force: bool, no_migration: bool, light: bool = False):
    click.echo(f"Downloading in {str(path)}.")
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
    
    # Choix de l'URL à télécharger
    if light:
        click.echo("Downloading light version of dataset...")
        download_url = LIGHT_DATASET_URL
    else:
        click.echo("Downloading full version of dataset...")
        download_url = DATASET_URL

    # Téléchargement du dataset
    download_file(download_url, archive_path)
    
    # Extraction de l'archive
    click.echo("Extracting archive...")
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(path)
    
    # Suppression de l'archive
    archive_path.unlink()
    
    # Vérification de l'existence du dataset avant migration
    if not dataset_path.exists():
        click.echo(f"Error: Expected dataset path {dataset_path} doesn't exist after extraction")
        click.echo("Retrying with full dataset URL...")
        return
        
    # Migration du dataset si nécessaire
    if not no_migration:
        try:
            click.echo("Migrating dataset...")
            migrate_dataset(dataset_path, False)
        except Exception as e:
            click.echo(f"Error during migration: {str(e)}")
