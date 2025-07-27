from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, PrimaryKeyConstraint, func, Date, cast
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import csv
from datetime import date, timedelta, datetime
import json

os.makedirs('dados', exist_ok=True)
db = create_engine("sqlite:///dados/spotify_data.db")
Session = sessionmaker(bind=db)
session = Session()

Base = declarative_base()

class Artistas(Base):
    __tablename__ = 'artistas'
    id_artista = Column(String, primary_key=True)
    nome_artista = Column(String)

    def __repr__(self):
        return f'<Artista(id_artista="{self.id_artista}", nome_artista="{self.nome_artista}")>'

class TopTracks(Base):
    __tablename__ = 'top_tracks'
    nome_musica = Column(String)
    id_musica = Column(String)
    popularidade = Column(Integer)
    album = Column(String)
    id_artista = Column(String, ForeignKey('artistas.id_artista'))
    data_insercao = Column(String)
    __table_args__ = (PrimaryKeyConstraint('id_musica', 'data_insercao'),)

    def __repr__(self):
        return (f'<TopTracks(nome_musica="{self.nome_musica}", id_musica="{self.id_musica}", '
                f'popularidade={self.popularidade}, album="{self.album}", '
                f'id_artista="{self.id_artista}", data_insercao="{self.data_insercao}")>')

Base.metadata.create_all(bind=db)

class BancoDeDados:
    def checagem_data_dados(self, artista_json):
        """
        Verifica se existem dados para cada artista presente no JSON para a data atual.

        Returns:
            list: Lista de artistas sem dados atualizados para o dia atual.
        """
        try:
            with open(artista_json, 'r', encoding='utf-8') as f:
                artistas = json.load(f)
        except Exception as e:
            raise Exception(f'Erro ao processar ou ler o arquivo {artista_json}: {e}')

        try:
            hoje = str(date.today().strftime('%Y-%m-%d'))
            artistas_sem_dados = list()

            for artista in artistas:
                existe = session.query(TopTracks).join(Artistas).filter(
                    func.lower(Artistas.nome_artista) == artista.lower(),
                    TopTracks.data_insercao.like(f'{hoje}%')
                ).first()
                if not existe:
                    artistas_sem_dados.append(artista)


        except Exception as e:
            raise Exception(f'Erro ao consultar o banco de dados: {e}')
        
        return artistas_sem_dados

    def criar_csv(self, resultados):
        """
        Cria um arquivo CSV com os resultados das tracks dos artistas.

        Args:
            resultados (list): Lista de dicionários contendo informacoes dos artistas e tracks.
        """
        try:
            subpasta = 'dados'
            caminho_completo = os.path.join(subpasta, f'resultado_pesquisas_{date.today()}.csv')
            arquivo_existe = os.path.exists(caminho_completo)
            escrever_header = not arquivo_existe or os.path.getsize(caminho_completo) == 0

            data_insecao_atual = datetime.now()

            with open(caminho_completo, 'a', newline='', encoding='utf-8') as f:
                colunas = ['nome_artista', 'id_artista', 'nome_musica', 'id_musica', 'popularidade', 'album', 'data_insercao']

                writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')

                if escrever_header:
                    writer.writeheader()

                for artista_info in resultados:
                    artista = artista_info['artista']
                    for track in artista_info['top_tracks']:
                        writer.writerow({
                            'nome_artista': artista.nome,
                            'id_artista': artista.id_artista,
                            'nome_musica': track.nome_track,
                            'id_musica': track.id_track,
                            'popularidade': track.popularidade,
                            'album': track.album,
                            'data_insercao': data_insecao_atual
                        })
        except Exception as e:
            print(e)
            return

    def inserir_dados_csv_no_banco(self, pasta_csv='dados'):
        """
        Lê todos os arquivos CSV da pasta especificada e insere os dados no banco de dados.

        Args:
            pasta_csv (str): Caminho da pasta onde estão os arquivos CSV. Padrão é 'dados'.
        """
        try:
            for arquivo in os.listdir(pasta_csv):
                if arquivo.endswith('.csv'):
                    caminho_completo = os.path.join(pasta_csv, arquivo)
                    with open(caminho_completo, encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter=';')
                        if reader.fieldnames is None:
                            raise RuntimeError(f'O arquivo CSV {arquivo} está vazio ou sem cabeçalho.')
                        linhas = list(reader)
                        if not linhas:
                            raise RuntimeError(f'O arquivo CSV {arquivo} está vazio.')
                        for row in linhas:
                            artista_obj = Artistas(
                                id_artista = row['id_artista'],
                                nome_artista=row['nome_artista']
                            )
                            session.merge(artista_obj)

                            track_obj = TopTracks(
                                nome_musica=row['nome_musica'],
                                id_musica=row['id_musica'],
                                popularidade=int(row['popularidade']),
                                album=row['album'],
                                id_artista=row['id_artista'],
                                data_insercao=row['data_insercao']
                            )
                            session.merge(track_obj)
                        session.commit()
        except Exception as e:
            raise RuntimeError(f'Erro ao inserir dados do CSV {arquivo}: {e}')

    def consultar_dados_artistas(self, filtro):
        """
        Buscar artistas e suas top tracks no banco de dados pelo nome (case-insensitive) ou id exato.

        Args:
            filtro (list): Lista de nomes ou ids dos artistas.

        Return:
            list: Lista de objetos Artistas encontrados.
        """
        if not filtro:
            return session.query(Artistas).all()
        
        filtro_lower = [nome.lower() for nome in filtro]

        info_artistas = session.query(Artistas).filter(
            (func.lower(Artistas.nome_artista).in_(filtro_lower)) |
            (Artistas.id_artista.in_(filtro))
        ).all()

        return info_artistas

    def consultar_dados_top_tracks(self, id_artista):
        """
        Buscar top tracks e suas informacoes pelo id.

        Args:
            id_artista (str): ID do artista.

        Returns:
            list: Lista de objetos TopTracks do artista, ordenadas por popularidade (decrescente).
        """
        data_mais_recente = session.query(func.max(TopTracks.data_insercao)).filter(
            TopTracks.id_artista == id_artista
        ).scalar()

        tracks = session.query(TopTracks).filter(
            TopTracks.id_artista == id_artista,
            TopTracks.data_insercao == data_mais_recente
        ).order_by(TopTracks.popularidade.desc()).all()

        return tracks

    def exibir_artistas(self):
        """
        Exibe todos os artistas cadastrados no banco, ordenados alfabeticamente.
        Retorna True se houver artistas, False se não houver.
        """
        todos = self.consultar_dados_artistas([])
        if not todos:
            raise RuntimeError('Nenhum artista encontrado no banco. Execute com --artistas_json para atualizar os dados.')
        print('\nTodos os artistas do banco:\n')
        for artista in sorted(todos, key=lambda a: a.nome_artista.lower()):
            print(f'{artista.id_artista} - {artista.nome_artista}')
