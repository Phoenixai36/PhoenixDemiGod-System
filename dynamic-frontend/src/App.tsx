import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, Route, Routes } from "react-router-dom";
import GenericPage from "./pages/GenericPage";
import { fetchAppConfig } from "./store/appConfigSlice";
import { AppDispatch, RootState } from "./store/store";

function App() {
  const dispatch = useDispatch<AppDispatch>();
  const { navigation, status } = useSelector(
    (state: RootState) => state.appConfig
  );

  useEffect(() => {
    if (status === "idle") {
      dispatch(fetchAppConfig());
    }
  }, [status, dispatch]);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Barra de navegación lateral */}
      <aside className="w-64 bg-gray-800 text-white">
        <div className="p-4 font-bold text-lg">Mi App</div>
        <nav>
          <ul>
            {navigation.map((item) => (
              <li key={item.id}>
                <Link to={item.path} className="block p-4 hover:bg-gray-700">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Contenido principal */}
      <main className="flex-1 p-10">
        <Routes>
          <Route path="/page/:pageName" element={<GenericPage />} />
          {/* Ruta de bienvenida */}
          <Route
            path="/"
            element={
              <div>
                <h1>Bienvenido</h1>
                <p>Selecciona una opción del menú.</p>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
