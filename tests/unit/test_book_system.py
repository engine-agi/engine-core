""""""

Testes para o Sistema de Book - Gestao Hierarquica de Memoria.Testes para o Sistema de Book - Gestao Hierarquica de Memoria.



Testes baseados nos principios reais de funcionamento do sistema:Testes baseados nos principios reais de funcionamento do sistema:

- BookBuilder cria Books usando padrao Builder- BookBuilder cria Books usando padrao Builder

- Books contem Chapters (capitulos)- Books contem Chapters (capitulos)

- Chapters contem Pages (paginas)- Chapters contem Pages (paginas)

- Pages contem Sections (secoes)- Pages contem Sections (secoes)

- Sistema de busca semantica integrado- Sistema de busca semantica integrado

""""""



import pytestimport pytest



from engine_core.core.book.book_builder import (from engine_core.core.book.book_builder import (

    AccessLevel,    AccessLevel,

    Book,    Book,

    BookBuilder,    BookBuilder,

    BookChapter,    BookChapter,

    BookPage,    BookPage,

    ContentSection,    ContentSection,

    ContentStatus,    ContentStatus,

    ContentType,    ContentType,

    SearchQuery,    SearchQuery,

    SearchResult,    SearchResult,

    SearchScope,    SearchScope,

    SemanticSearchEngine,    SemanticSearchEngine,

))





class TestBookBuilder:class TestBookBuilder:

    """Testa o BookBuilder e criacao de Books."""    """Testa o BookBuilder e criacao de Books."""



    def test_builder_initialization(self):    def test_builder_initialization(self):

        """Testa inicializacao do builder."""        """Testa inicializacao do builder."""

        builder = BookBuilder()        builder = BookBuilder()

        assert builder._book_id is None        assert builder._book_id is None

        assert builder._title is None        assert builder._title is None

        assert builder._description == ""        assert builder._description == ""

        assert builder._is_public is False        assert builder._is_public is False

        assert builder._enable_versioning is True        assert builder._enable_versioning is True

        assert builder._enable_search is True        assert builder._enable_search is True



    def test_builder_fluent_interface(self):    def test_builder_fluent_interface(self):

        """Testa interface fluente do builder."""        """Testa interface fluente do builder."""

        builder = BookBuilder()        builder = BookBuilder()

        result = (        result = (

            builder            builder

            .with_id("test_book")            .with_id("test_book")

            .with_title("Test Book")            .with_title("Test Book")

            .with_description("Test description")            .with_description("Test description")

            .with_author("Test Author")            .with_author("Test Author")

            .with_project("test_project")            .with_public_access(True)

            .with_public_access(True)        )

            .with_comments_enabled(True)        assert result is builder

            .add_tags(["test", "book"])        assert builder._book_id == "test_book"

            .add_categories(["tech", "guide"])        assert builder._title == "Test Book"

            .build()        assert builder._description == "Test description"

        )        assert builder._author == "Test Author"

        assert builder._is_public is True

        assert isinstance(result, Book)

        assert result.book_id == "test_book"    def test_build_without_required_fields_fails(self):

        assert result.title == "Test Book"        """Testa que build falha sem campos obrigatorios."""

        assert result.description == "Test description"        builder = BookBuilder()

        assert result.author == "Test Author"

        assert result.project_id == "test_project"        # Sem ID

        assert result.is_public is True        with pytest.raises(ValueError, match="Book ID is required"):

        assert result.allow_comments is True            builder.with_title("Test").build()

        assert "test" in result.tags

        assert "book" in result.tags        # Sem titulo

        assert "tech" in result.categories        with pytest.raises(ValueError, match="Book title is required"):

        assert "guide" in result.categories            builder.with_id("test").build()



    def test_builder_reset_after_build(self):    def test_build_basic_book(self):

        """Testa que builder reseta apos build."""        """Testa criacao de livro basico."""

        builder = BookBuilder()        book = BookBuilder().with_id("basic_book").with_title("Basic Book").build()

        builder.with_id("test").with_title("Test")

        assert isinstance(book, Book)

        book1 = builder.build()        assert book.book_id == "basic_book"

        assert book1.book_id == "test"        assert book.title == "Basic Book"

        assert book.description == ""

        # Builder deve estar resetado        assert book.author is None

        assert builder._book_id is None        assert book.is_public is False

        assert builder._title is None        assert len(book.chapters) == 0



        # Pode criar outro livro    def test_build_complete_book(self):

        book2 = builder.with_id("test2").with_title("Test 2").build()        """Testa criacao de livro completo."""

        assert book2.book_id == "test2"        book = (

            BookBuilder()

            .with_id("complete_book")

class TestBookHierarchy:            .with_title("Complete Book")

    """Testa a hierarquia Book -> Chapter -> Page -> Section."""            .with_description("A complete test book")

            .with_author("Test Author")

    @pytest.fixture            .with_project("test_project")

    def sample_book(self):            .with_public_access(True)

        """Cria um livro de exemplo para testes."""            .with_comments_enabled(True)

        book = (            .add_tags(["test", "documentation"])

            BookBuilder()            .add_categories(["tech", "guide"])

            .with_id("hierarchy_test")            .build()

            .with_title("Hierarchy Test Book")        )

            .with_description("Book for testing hierarchy")

            .build()        assert book.book_id == "complete_book"

        )        assert book.title == "Complete Book"

        assert book.description == "A complete test book"

        # Adiciona capitulos        assert book.author == "Test Author"

        intro = book.add_chapter("Introducao", "Capitulo introdutorio")        assert book.project_id == "test_project"

        concepts = book.add_chapter("Conceitos", "Conceitos basicos")        assert book.is_public is True

        assert book.allow_comments is True

        # Adiciona paginas aos capitulos        assert "test" in book.tags

        welcome = intro.add_page("Boas-vindas", "Pagina de boas-vindas")        assert "documentation" in book.tags

        overview = intro.add_page("Visao Geral", "Visao geral do livro")        assert "tech" in book.categories

        assert "guide" in book.categories

        variables = concepts.add_page("Variaveis", "Conceitos de variaveis")

        functions = concepts.add_page("Funcoes", "Conceitos de funcoes")    def test_builder_reset_after_build(self):

        """Testa que builder reseta apos build."""

        # Adiciona secoes as paginas        builder = BookBuilder()

        welcome.add_section("Saudacao", "Ola e bem-vindo!")        builder.with_id("test").with_title("Test")

        welcome.add_section("Objetivos", "Objetivos do livro")

        book1 = builder.build()

        variables.add_section("Definicao", "Variaveis armazenam dados")        assert book1.book_id == "test"

        variables.add_section("Tipos", "Tipos de variaveis em Python")

        # Builder deve estar resetado

        return book        assert builder._book_id is None

        assert builder._title is None

    def test_book_creation(self, sample_book):

        """Testa criacao basica do livro."""        # Pode criar outro livro

        assert sample_book.book_id == "hierarchy_test"        book2 = builder.with_id("test2").with_title("Test 2").build()

        assert sample_book.title == "Hierarchy Test Book"        assert book2.book_id == "test2"

        assert len(sample_book.chapters) == 2



    def test_chapter_operations(self, sample_book):class TestBookHierarchy:

        """Testa operacoes com capitulos."""    """Testa a hierarquia Book -> Chapter -> Page -> Section."""

        # Verifica capitulos criados

        intro = sample_book.get_chapter("hierarchy_test_chapter_1")    @pytest.fixture

        concepts = sample_book.get_chapter("hierarchy_test_chapter_2")    def sample_book(self):

        """Cria um livro de exemplo para testes."""

        assert intro is not None        book = (

        assert intro.title == "Introducao"            BookBuilder()

        assert concepts is not None            .with_id("hierarchy_test")

        assert concepts.title == "Conceitos"            .with_title("Hierarchy Test Book")

            .with_description("Book for testing hierarchy")

        # Testa adicao de novo capitulo            .build()

        conclusion = sample_book.add_chapter("Conclusao", "Capitulo final")        )

        assert len(sample_book.chapters) == 3

        assert conclusion.title == "Conclusao"        # Adiciona capitulos

        intro = book.add_chapter("Introducao", "Capitulo introdutorio")

        # Testa remocao de capitulo        concepts = book.add_chapter("Conceitos", "Conceitos basicos")

        success = sample_book.remove_chapter("hierarchy_test_chapter_1")

        assert success        # Adiciona paginas aos capitulos

        assert len(sample_book.chapters) == 2        welcome = intro.add_page("Boas-vindas", "Pagina de boas-vindas")

        assert sample_book.get_chapter("hierarchy_test_chapter_1") is None        overview = intro.add_page("Visao Geral", "Visao geral do livro")



    def test_page_operations(self, sample_book):        variables = concepts.add_page("Variaveis", "Conceitos de variaveis")

        """Testa operacoes com paginas."""        functions = concepts.add_page("Funcoes", "Conceitos de funcoes")

        intro = sample_book.get_chapter("hierarchy_test_chapter_1")

        assert intro is not None        # Adiciona secoes as paginas

        welcome.add_section("Saudacao", "Ola e bem-vindo!")

        # Verifica paginas criadas        welcome.add_section("Objetivos", "Objetivos do livro")

        welcome = intro.get_page("hierarchy_test_chapter_1_page_1")

        overview = intro.get_page("hierarchy_test_chapter_1_page_2")        variables.add_section("Definicao", "Variaveis armazenam dados")

        variables.add_section("Tipos", "Tipos de variaveis em Python")

        assert welcome is not None

        assert welcome.title == "Boas-vindas"        return book

        assert overview is not None

        assert overview.title == "Visao Geral"    def test_book_creation(self, sample_book):

        """Testa criacao basica do livro."""

        # Testa acesso via book        assert sample_book.book_id == "hierarchy_test"

        welcome_from_book = sample_book.get_page("hierarchy_test_chapter_1_page_1")        assert sample_book.title == "Hierarchy Test Book"

        assert welcome_from_book is welcome        assert len(sample_book.chapters) == 2



    def test_section_operations(self, sample_book):    def test_chapter_operations(self, sample_book):

        """Testa operacoes com secoes."""        """Testa operacoes com capitulos."""

        welcome = sample_book.get_page("hierarchy_test_chapter_1_page_1")        # Verifica capitulos criados

        assert welcome is not None        intro = sample_book.get_chapter("hierarchy_test_chapter_1")

        concepts = sample_book.get_chapter("hierarchy_test_chapter_2")

        # Verifica secoes criadas

        greeting = welcome.get_section("hierarchy_test_chapter_1_page_1_section_1")        assert intro is not None

        objectives = welcome.get_section("hierarchy_test_chapter_1_page_1_section_2")        assert intro.title == "Introducao"

        assert concepts is not None

        assert greeting is not None        assert concepts.title == "Conceitos"

        assert greeting.title == "Saudacao"

        assert greeting.content == "Ola e bem-vindo!"        # Testa adicao de novo capitulo

        assert objectives is not None        conclusion = sample_book.add_chapter("Conclusao", "Capitulo final")

        assert objectives.title == "Objetivos"        assert len(sample_book.chapters) == 3

        assert conclusion.title == "Conclusao"

        # Testa acesso via book

        greeting_from_book = sample_book.get_section("hierarchy_test_chapter_1_page_1_section_1")        # Testa remocao de capitulo

        assert greeting_from_book is greeting        success = sample_book.remove_chapter("hierarchy_test_chapter_1")

        assert success

    def test_content_navigation(self, sample_book):        assert len(sample_book.chapters) == 2

        """Testa navegacao completa pela hierarquia."""        assert sample_book.get_chapter("hierarchy_test_chapter_1") is None

        # Navega: Book -> Chapter -> Page -> Section

        chapter = sample_book.chapters[0]    def test_page_operations(self, sample_book):

        page = chapter.pages[0]        """Testa operacoes com paginas."""

        section = page.sections[0]        intro = sample_book.get_chapter("hierarchy_test_chapter_1")

        assert intro is not None

        assert chapter.book_id == sample_book.book_id

        assert page.chapter_id == chapter.chapter_id        # Verifica paginas criadas

        assert section.parent_page_id == page.page_id        welcome = intro.get_page("hierarchy_test_chapter_1_page_1")

        overview = intro.get_page("hierarchy_test_chapter_1_page_2")

    def test_content_updates(self, sample_book):

        """Testa atualizacoes de conteudo."""        assert welcome is not None

        section = sample_book.get_section("hierarchy_test_chapter_1_page_1_section_1")        assert welcome.title == "Boas-vindas"

        assert section is not None        assert overview is not None

        assert overview.title == "Visao Geral"

        original_version = section.metadata.version

        # Testa acesso via book

        # Atualiza conteudo        welcome_from_book = sample_book.get_page("hierarchy_test_chapter_1_page_1")

        section.update_content("Conteudo atualizado!", "usuario_teste")        assert welcome_from_book is welcome



        assert section.content == "Conteudo atualizado!"    def test_section_operations(self, sample_book):

        assert section.metadata.version == original_version + 1        """Testa operacoes com secoes."""

        assert section.metadata.updated_by == "usuario_teste"        welcome = sample_book.get_page("hierarchy_test_chapter_1_page_1")

        assert welcome is not None



class TestSemanticSearch:        # Verifica secoes criadas

    """Testa funcionalidade de busca semantica."""        greeting = welcome.get_section("hierarchy_test_chapter_1_page_1_section_1")

        objectives = welcome.get_section("hierarchy_test_chapter_1_page_1_section_2")

    @pytest.fixture

    def search_engine(self):        assert greeting is not None

        """Cria engine de busca para testes."""        assert greeting.title == "Saudacao"

        return SemanticSearchEngine(enable_embeddings=False)        assert greeting.content == "Ola e bem-vindo!"

        assert objectives is not None

    @pytest.fixture        assert objectives.title == "Objetivos"

    def book_with_content(self):

        """Cria livro com conteudo para testes de busca."""        # Testa acesso via book

        book = (        greeting_from_book = sample_book.get_section("hierarchy_test_chapter_1_page_1_section_1")

            BookBuilder()        assert greeting_from_book is greeting

            .with_id("search_test")

            .with_title("Livro de Busca")    def test_content_navigation(self, sample_book):

            .with_description("Livro para testes de busca semantica")        """Testa navegacao completa pela hierarquia."""

            .build()        # Navega: Book -> Chapter -> Page -> Section

        )        chapter = sample_book.chapters[0]

        page = chapter.pages[0]

        # Adiciona conteudo        section = page.sections[0]

        chapter = book.add_chapter("Python", "Conceitos de Python")

        page1 = chapter.add_page("Sintaxe", "Sintaxe basica do Python")        assert chapter.book_id == sample_book.book_id

        page1.add_section("Variaveis", "Variaveis armazenam valores")        assert page.chapter_id == chapter.chapter_id

        page1.add_section("Funcoes", "Funcoes sao blocos reutilizaveis")        assert section.parent_page_id == page.page_id



        page2 = chapter.add_page("OO", "Programacao orientada a objetos")    def test_content_updates(self, sample_book):

        page2.add_section("Classes", "Classes definem objetos")        """Testa atualizacoes de conteudo."""

        page2.add_section("Heranca", "Heranca permite reutilizacao")        section = sample_book.get_section("hierarchy_test_chapter_1_page_1_section_1")

        assert section is not None

        return book

        original_version = section.metadata.version

    def test_search_engine_initialization(self, search_engine):

        """Testa inicializacao da engine de busca."""        # Atualiza conteudo

        assert search_engine.enable_embeddings is False        section.update_content("Conteudo atualizado!", "usuario_teste")

        assert len(search_engine.content_index) == 0

        assert len(search_engine.inverted_index) == 0        assert section.content == "Conteudo atualizado!"

        assert section.metadata.version == original_version + 1

    def test_index_book_content(self, search_engine, book_with_content):        assert section.metadata.updated_by == "usuario_teste"

        """Testa indexacao de conteudo do livro."""

        # Indexar todo o conteudo do livro

        for chapter in book_with_content.chapters:class TestSemanticSearch:

            for page in chapter.pages:    """Testa funcionalidade de busca semantica."""

                for section in page.sections:

                    search_engine.index_content(    @pytest.fixture

                        content_id=section.section_id,    def search_engine(self):

                        content_type="section",        """Cria engine de busca para testes."""

                        title=section.title,        return SemanticSearchEngine(enable_embeddings=False)

                        content=section.content,

                        metadata=section.metadata    @pytest.fixture

                    )    def book_with_content(self):

        """Cria livro com conteudo para testes de busca."""

        # Verifica que conteudo foi indexado        book = (

        assert len(search_engine.content_index) > 0            BookBuilder()

            .with_id("search_test")

        # Verifica inverted index            .with_title("Livro de Busca")

        assert len(search_engine.inverted_index) > 0            .with_description("Livro para testes de busca semantica")

            .build()

    def test_search_in_book(self, search_engine, book_with_content):        )

        """Testa busca dentro do livro."""

        # Indexar conteudo primeiro        # Adiciona conteudo

        for chapter in book_with_content.chapters:        chapter = book.add_chapter("Python", "Conceitos de Python")

            for page in chapter.pages:        page1 = chapter.add_page("Sintaxe", "Sintaxe basica do Python")

                for section in page.sections:        page1.add_section("Variaveis", "Variaveis armazenam valores")

                    search_engine.index_content(        page1.add_section("Funcoes", "Funcoes sao blocos reutilizaveis")

                        content_id=section.section_id,

                        content_type="section",        page2 = chapter.add_page("OO", "Programacao orientada a objetos")

                        title=section.title,        page2.add_section("Classes", "Classes definem objetos")

                        content=section.content,        page2.add_section("Heranca", "Heranca permite reutilizacao")

                        metadata=section.metadata

                    )        return book



        query = SearchQuery(    def test_search_engine_initialization(self, search_engine):

            query_text="funcoes",        """Testa inicializacao da engine de busca."""

            max_results=10,        assert search_engine.enable_embeddings is False

            semantic_search=False        assert len(search_engine.content_index) == 0

        )        assert len(search_engine.inverted_index) == 0



        results = search_engine.search(query, book_with_content)    def test_index_book_content(self, search_engine, book_with_content):

        assert isinstance(results, list)        """Testa indexacao de conteudo do livro."""

        search_engine.index_book(book_with_content)

        # Deve encontrar resultados relacionados a funcoes

        if len(results) > 0:        # Verifica que conteudo foi indexado

            for result in results:        assert len(search_engine.content_index) > 0

                assert isinstance(result, SearchResult)

                assert result.relevance_score >= 0        # Verifica inverted index

        assert len(search_engine.inverted_index) > 0

    def test_search_with_different_scopes(self, search_engine, book_with_content):

        """Testa busca com diferentes escopos."""    def test_search_in_book(self, search_engine, book_with_content):

        # Indexar conteudo primeiro        """Testa busca dentro do livro."""

        for chapter in book_with_content.chapters:        search_engine.index_book(book_with_content)

            for page in chapter.pages:

                for section in page.sections:        query = SearchQuery(

                    search_engine.index_content(            query_text="funcoes",

                        content_id=section.section_id,            scope=SearchScope.BOOK,

                        content_type="section",            scope_id=book_with_content.book_id

                        title=section.title,        )

                        content=section.content,

                        metadata=section.metadata        results = search_engine.search(query, book_with_content)

                    )        assert isinstance(results, list)



        # Busca global        # Deve encontrar resultados relacionados a funcoes

        global_query = SearchQuery(        if len(results) > 0:

            query_text="python",            for result in results:

            max_results=10,                assert isinstance(result, SearchResult)

            semantic_search=False                assert result.relevance_score >= 0

        )

        global_results = search_engine.search(global_query, book_with_content)    def test_search_with_different_scopes(self, search_engine, book_with_content):

        """Testa busca com diferentes escopos."""

        # Busca no livro        search_engine.index_book(book_with_content)

        book_query = SearchQuery(

            query_text="python",        # Busca global

            max_results=10,        global_query = SearchQuery(

            semantic_search=False            query_text="python",

        )            scope=SearchScope.GLOBAL

        book_results = search_engine.search(book_query, book_with_content)        )

        global_results = search_engine.search(global_query, book_with_content)

        # Resultados devem ser listas

        assert isinstance(global_results, list)        # Busca no livro

        assert isinstance(book_results, list)        book_query = SearchQuery(

            query_text="python",

    def test_empty_search_results(self, search_engine):            scope=SearchScope.BOOK,

        """Testa resultados vazios de busca."""            scope_id=book_with_content.book_id

        query = SearchQuery(query_text="termo_inexistente", max_results=10, semantic_search=False)        )

        results = search_engine.search(query, Book("test", "Test"))        book_results = search_engine.search(book_query, book_with_content)



        assert results == []        # Resultados devem ser listas

        assert isinstance(global_results, list)

        assert isinstance(book_results, list)

class TestContentManagement:

    """Testa gerenciamento de conteudo."""    def test_empty_search_results(self, search_engine):

        """Testa resultados vazios de busca."""

    def test_content_section_creation(self):        query = SearchQuery(query_text="termo_inexistente")

        """Testa criacao de secao de conteudo."""        results = search_engine.search(query, Book("test", "Test"))

        section = ContentSection(

            section_id="test_section",        assert results == []

            title="Secao de Teste",

            content="Conteudo de teste",

            content_type=ContentType.TEXTclass TestContentManagement:

        )    """Testa gerenciamento de conteudo."""



        assert section.section_id == "test_section"    def test_content_section_creation(self):

        assert section.title == "Secao de Teste"        """Testa criacao de secao de conteudo."""

        assert section.content == "Conteudo de teste"        section = ContentSection(

        assert section.content_type == ContentType.TEXT            section_id="test_section",

        assert section.metadata.version == 1            title="Secao de Teste",

        assert section.metadata.status == ContentStatus.DRAFT            content="Conteudo de teste",

            content_type=ContentType.TEXT

    def test_content_versioning(self):        )

        """Testa versionamento de conteudo."""

        section = ContentSection(        assert section.section_id == "test_section"

            section_id="version_test",        assert section.title == "Secao de Teste"

            title="Teste de Versao",        assert section.content == "Conteudo de teste"

            content="Conteudo inicial"        assert section.content_type == ContentType.TEXT

        )        assert section.metadata.version == 1

        assert section.metadata.status == ContentStatus.DRAFT

        # Estado inicial

        assert section.metadata.version == 1    def test_content_versioning(self):

        initial_updated = section.metadata.updated_at        """Testa versionamento de conteudo."""

        section = ContentSection(

        # Primeira atualizacao            section_id="version_test",

        section.update_content("Conteudo v2", "autor1")            title="Teste de Versao",

        assert section.metadata.version == 2            content="Conteudo inicial"

        assert section.metadata.updated_by == "autor1"        )



        # Segunda atualizacao        # Estado inicial

        section.update_content("Conteudo v3", "autor2")        assert section.metadata.version == 1

        assert section.metadata.version == 3        initial_updated = section.metadata.updated_at

        assert section.metadata.updated_by == "autor2"

        assert section.metadata.updated_at > initial_updated        # Primeira atualizacao

        section.update_content("Conteudo v2", "autor1")

    def test_content_checksum(self):        assert section.metadata.version == 2

        """Testa calculo de checksum."""        assert section.metadata.updated_by == "autor1"

        section = ContentSection(

            section_id="checksum_test",        # Segunda atualizacao

            title="Teste Checksum",        section.update_content("Conteudo v3", "autor2")

            content="Conteudo para teste"        assert section.metadata.version == 3

        )        assert section.metadata.updated_by == "autor2"

        assert section.metadata.updated_at > initial_updated

        # Checksum deve ser gerado

        assert section.metadata.checksum is not None    def test_content_checksum(self):

        assert len(section.metadata.checksum) > 0        """Testa calculo de checksum."""

        section = ContentSection(

        # Checksum deve mudar com conteudo            section_id="checksum_test",

        original_checksum = section.metadata.checksum            title="Teste Checksum",

        section.update_content("Conteudo modificado")            content="Conteudo para teste"

        assert section.metadata.checksum != original_checksum        )



        # Checksum deve ser gerado

class TestPersistenceAndStorage:        assert section.metadata.checksum is not None

    """Testa persistencia e armazenamento."""        assert len(section.metadata.checksum) > 0



    def test_book_serialization(self):        # Checksum deve mudar com conteudo

        """Testa serializacao do livro."""        original_checksum = section.metadata.checksum

        book = (        section.update_content("Conteudo modificado")

            BookBuilder()        assert section.metadata.checksum != original_checksum

            .with_id("serialization_test")

            .with_title("Livro de Serializacao")

            .with_description("Teste de serializacao")class TestIntegration:

            .build()    """Testa integracao completa do sistema."""

        )

    def test_complete_book_workflow(self):

        # Adiciona algum conteudo        """Testa workflow completo de criacao e uso."""

        chapter = book.add_chapter("Teste", "Capitulo de teste")        # 1. Criar livro

        page = chapter.add_page("Pagina", "Pagina de teste")        book = (

        page.add_section("Secao", "Conteudo de teste")            BookBuilder()

            .with_id("workflow_complete")

        # Serializa            .with_title("Workflow Completo")

        book_dict = book.to_dict()            .with_description("Teste de workflow completo")

            .with_author("Sistema de Teste")

        assert isinstance(book_dict, dict)            .build()

        assert book_dict["book_id"] == "serialization_test"        )

        assert book_dict["title"] == "Livro de Serializacao"

        assert len(book_dict["chapters"]) == 1        # 2. Construir hierarquia

        intro = book.add_chapter("Introducao", "Capitulo introdutorio")

    def test_book_statistics(self):        welcome = intro.add_page("Bem-vindo", "Pagina de boas-vindas")

        """Testa calculo de estatisticas do livro."""        welcome.add_section("Saudacao", "Ola!")

        book = (        welcome.add_section("Sobre", "Sobre este livro")

            BookBuilder()

            .with_id("stats_test")        # 3. Verificar estrutura

            .with_title("Livro de Estatisticas")        assert len(book.chapters) == 1

            .build()        assert len(book.chapters[0].pages) == 1

        )        assert len(book.chapters[0].pages[0].sections) == 2



        # Adiciona conteudo        # 4. Testar navegacao

        chapter1 = book.add_chapter("Cap1", "Primeiro capitulo")        section = book.get_section("workflow_complete_chapter_1_page_1_section_1")

        page1 = chapter1.add_page("Pag1", "Primeira pagina")        assert section is not None

        page1.add_section("Sec1", "Primeira secao com conteudo")        assert section.title == "Saudacao"

        page1.add_section("Sec2", "Segunda secao com mais conteudo aqui")

        # 5. Testar busca

        chapter2 = book.add_chapter("Cap2", "Segundo capitulo")        search_engine = SemanticSearchEngine(enable_embeddings=False)

        page2 = chapter2.add_page("Pag2", "Segunda pagina")        search_engine.index_book(book)

        page2.add_section("Sec3", "Terceira secao")

        query = SearchQuery(

        # Calcula estatisticas            query_text="ola",

        stats = book.get_statistics()            scope=SearchScope.BOOK,

            scope_id=book.book_id

        assert isinstance(stats, dict)        )

        assert stats["chapter_count"] == 2        results = search_engine.search(query, book)

        assert stats["page_count"] == 2        assert isinstance(results, list)

        assert stats["section_count"] == 3

        assert stats["word_count"] > 0    def test_content_lifecycle(self):

        assert stats["character_count"] > 0        """Testa ciclo de vida completo do conteudo."""

        # Criar secao

        section = ContentSection(

class TestIntegration:            section_id="lifecycle",

    """Testa integracao completa do sistema."""            title="Ciclo de Vida",

            content="Conteudo inicial"

    def test_complete_book_workflow(self):        )

        """Testa workflow completo de criacao e uso."""

        # 1. Criar livro        # Verificar estado inicial

        book = (        assert section.metadata.status == ContentStatus.DRAFT

            BookBuilder()        assert section.metadata.version == 1

            .with_id("workflow_complete")

            .with_title("Workflow Completo")        # Atualizar varias vezes

            .with_description("Teste de workflow completo")        section.update_content("Conteudo rascunho", "autor1")

            .with_author("Sistema de Teste")        assert section.metadata.version == 2

            .build()

        )        section.update_content("Conteudo final", "autor2")

        assert section.metadata.version == 3

        # 2. Construir hierarquia

        intro = book.add_chapter("Introducao", "Capitulo introdutorio")        # Verificar historico de atualizacoes

        welcome = intro.add_page("Bem-vindo", "Pagina de boas-vindas")        assert section.metadata.updated_by == "autor2"

        welcome.add_section("Saudacao", "Ola!")        assert section.metadata.updated_at is not None

        welcome.add_section("Sobre", "Sobre este livro")

import pytest

        # 3. Verificar estrutura

        assert len(book.chapters) == 1from engine_core.core.book.book_builder import (

        assert len(book.chapters[0].pages) == 1    Book,

        assert len(book.chapters[0].pages[0].sections) == 2    BookBuilder,

    BookChapter,

        # 4. Testar navegacao    BookPage,

        section = book.get_section("workflow_complete_chapter_1_page_1_section_1")    ContentSection,

        assert section is not None    ContentType,

        assert section.title == "Saudacao"    ContentStatus,

)

        # 5. Testar busca

        search_engine = SemanticSearchEngine(enable_embeddings=False)

class TestBookBuilder:

        # Indexar conteudo    """Testa a funcionalidade do BookBuilder."""

        for chapter in book.chapters:

            for page in chapter.pages:    def test_book_builder_initialization(self):

                for section in page.sections:        """Testa se o builder inicializa com configuracao padrao."""

                    search_engine.index_content(        builder = BookBuilder()

                        content_id=section.section_id,        assert builder._book_id is None

                        content_type="section",        assert builder._title is None

                        title=section.title,        assert builder._description == ""

                        content=section.content,        assert builder._is_public is False

                        metadata=section.metadata        assert builder._enable_versioning is True

                    )        assert builder._enable_search is True



        query = SearchQuery(    def test_build_basic_book(self):

            query_text="ola",        """Testa construcao de um livro basico."""

            max_results=10,        book = BookBuilder().with_id("livro_basico").with_title("Livro Basico").build()

            semantic_search=False

        )        assert isinstance(book, Book)

        results = search_engine.search(query, book)        assert book.book_id == "livro_basico"

        assert isinstance(results, list)        assert book.title == "Livro Basico"

        assert len(book.chapters) == 0

    def test_content_lifecycle(self):

        """Testa ciclo de vida completo do conteudo."""    def test_build_complete_book(self):

        # Criar secao        """Testa construcao de um livro completo."""

        section = ContentSection(        book = (

            section_id="lifecycle",            BookBuilder()

            title="Ciclo de Vida",            .with_id("livro_completo")

            content="Conteudo inicial"            .with_title("Livro Completo")

        )            .with_description("Um livro completo para testes")

            .with_author("Autor Completo")

        # Verificar estado inicial            .with_project("projeto_completo")

        assert section.metadata.status == ContentStatus.DRAFT            .with_public_access(True)

        assert section.metadata.version == 1            .with_comments_enabled(True)

            .build()

        # Atualizar varias vezes        )

        section.update_content("Conteudo rascunho", "autor1")

        assert section.metadata.version == 2        assert book.book_id == "livro_completo"

        assert book.title == "Livro Completo"

        section.update_content("Conteudo final", "autor2")        assert book.description == "Um livro completo para testes"

        assert section.metadata.version == 3        assert book.author == "Autor Completo"

        assert book.project_id == "projeto_completo"

        # Verificar historico de atualizacoes        assert book.is_public is True

        assert section.metadata.updated_by == "autor2"        assert book.allow_comments is True

        assert section.metadata.updated_at is not None

class TestBookStructure:
    """Testa a estrutura hierarquica do Book."""

    @pytest.fixture
    def sample_book(self):
        """Cria um livro de exemplo para testes."""
        book = (
            BookBuilder()
            .with_id("livro_exemplo")
            .with_title("Livro de Exemplo")
            .with_description("Um livro para testes de estrutura")
            .build()
        )

        # Adiciona capitulos
        chapter1 = book.add_chapter("Introducao", "Introducao ao livro")
        chapter2 = book.add_chapter("Conceitos Basicos", "Conceitos fundamentais")

        # Adiciona paginas aos capitulos
        page1 = chapter1.add_page("Boas-vindas", "Bem-vindo ao livro")
        chapter1.add_page("Visao Geral", "Visao geral do conteudo")

        chapter2.add_page("Variaveis", "Conceitos de variaveis")
        chapter2.add_page("Funcoes", "Conceitos de funcoes")

        # Adiciona secoes as paginas
        page1.add_section("Saudacao", "Ola e bem-vindo!")
        page1.add_section("Proposito", "O proposito deste livro")

        return book

    def test_book_creation(self, sample_book):
        """Testa criacao basica do livro."""
        assert sample_book.book_id == "livro_exemplo"
        assert sample_book.title == "Livro de Exemplo"
        assert sample_book.description == "Um livro para testes de estrutura"
        assert len(sample_book.chapters) == 2

    def test_chapter_operations(self, sample_book):
        """Testa operacoes de capitulo."""
        # Testa obtencao de capitulo
        chapter1 = sample_book.get_chapter("livro_exemplo_chapter_1")
        assert chapter1 is not None
        assert chapter1.title == "Introducao"
        assert chapter1.description == "Introducao ao livro"

        # Testa adicao de capitulo
        new_chapter = sample_book.add_chapter("Conclusao", "Conclusao do livro")
        assert len(sample_book.chapters) == 3
        assert new_chapter.title == "Conclusao"

    def test_page_operations(self, sample_book):
        """Testa operacoes de pagina."""
        chapter1 = sample_book.get_chapter("livro_exemplo_chapter_1")
        assert chapter1 is not None

        # Testa obtencao de pagina
        page1 = sample_book.get_page("livro_exemplo_chapter_1_page_1")
        assert page1 is not None
        assert page1.title == "Boas-vindas"
        assert page1.description == "Bem-vindo ao livro"

    def test_section_operations(self, sample_book):
        """Testa operacoes de secao."""
        page1 = sample_book.get_page("livro_exemplo_chapter_1_page_1")
        assert page1 is not None

        # Testa obtencao de secao
        section1 = sample_book.get_section("livro_exemplo_chapter_1_page_1_section_1")
        assert section1 is not None
        assert section1.title == "Saudacao"
        assert section1.content == "Ola e bem-vindo!"


class TestContentManagement:
    """Testa gerenciamento de conteudo."""

    def test_content_section_creation(self):
        """Testa criacao de secao de conteudo."""
        section = ContentSection(
            section_id="section_test",
            title="Secao de Teste",
            content="Conteudo de teste",
            content_type=ContentType.TEXT
        )

        assert section.section_id == "section_test"
        assert section.title == "Secao de Teste"
        assert section.content == "Conteudo de teste"
        assert section.content_type == ContentType.TEXT
        assert section.metadata.version == 1
        assert section.metadata.status == ContentStatus.DRAFT

    def test_content_update(self):
        """Testa atualizacao de conteudo."""
        from datetime import datetime, UTC
        
        section = ContentSection(
            section_id="section_update",
            title="Secao para Atualizacao",
            content="Conteudo original"
        )
    
        original_version = section.metadata.version
        # Converte para timezone-aware para comparação
        original_updated = section.metadata.updated_at.replace(tzinfo=UTC) if section.metadata.updated_at.tzinfo is None else section.metadata.updated_at
    
        # Pequena pausa para garantir que o timestamp muda
        import time
        time.sleep(0.001)
    
        section.update_content("Conteudo atualizado", "usuario_teste")
    
        assert section.content == "Conteudo atualizado"
        assert section.metadata.version == original_version + 1
        assert section.metadata.updated_by == "usuario_teste"
        assert section.metadata.updated_at > original_updated